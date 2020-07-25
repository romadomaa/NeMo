# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This example demonstrates basic batch-based inference using NeMo's ASR model
"""

from argparse import ArgumentParser

from nemo.collections.asr.metrics.wer import WER, word_error_rate
from nemo.collections.asr.models import EncDecCTCModel
from nemo.utils import logging


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--asr_model",
        type=str,
        default="QuartzNet15x5-En",
        required=True,
        help="Pass: 'QuartzNet15x5-En', 'QuartzNet15x5-Zh', or 'JasperNet10x5-En'",
    )
    parser.add_argument("--dataset", type=str, required=True, help="path to evaluation data")
    parser.add_argument("--eval_batch_size", type=int, default=1, help="batch size to use for evaluation")
    parser.add_argument("--wer_target", type=float, default=None, help="used by test")
    parser.add_argument("--wer_tolerance", type=float, default=1.0, help="used by test")
    parser.add_argument("--trim_silence", default=True, type=bool, help="trim audio from silence or not")
    parser.add_argument(
        "--normalize_text", default=True, type=bool, help="Normalize transcripts or not. Set to False for non-English."
    )
    args = parser.parse_args()

    if args.asr_model.endswith('.nemo'):
        logging.info(f"Using local ASR model from {args.asr_model}")
        asr_model = EncDecCTCModel.restore_from(restore_path=args.asr_model)
    else:
        logging.info(f"Using NGC cloud ASR model {args.asr_model}")
        asr_model = EncDecCTCModel.from_pretrained(name=args.asr_model)
    asr_model.eval()

    asr_model.setup_test_data(
        test_data_config={
            'manifest_filepath': args.dataset,
            'sample_rate': 16000,
            'labels': asr_model.decoder.vocabulary,
            'batch_size': args.eval_batch_size,
            'trim_silence': args.trim_silence,
            'normalize_transcripts': args.normalize_text,
            'shuffle': False,
        }
    )
    wer = WER(vocabulary=asr_model.decoder.vocabulary)
    test_outs = []
    for test_batch in asr_model.test_dataloader():
        log_probs, encoded_len, greedy_predictions = asr_model(
            input_signal=test_batch[0], input_signal_length=test_batch[1]
        )
        test_outs.append(wer.ctc_decoder_predictions_tensor(greedy_predictions))
    print(test_outs)


if __name__ == '__main__':
    main()  # noqa pylint: disable=no-value-for-parameter