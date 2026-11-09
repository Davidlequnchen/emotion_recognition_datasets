# Copyright 2020 The HuggingFace Datasets Authors and the current dataset script contributor.
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

import csv
import os
import json 
import datasets

_CITATION = """\
"""

_DESCRIPTION = """\
Multidialog is the first large-sccale multimodal (i.e. audio, visual, and text) dialogue corpus, consisting of approximately 400 hours of audio-visual conversation strems between 6 pairs of conversation partners. 
It contina
"""

_HOMEPAGE = "https://multidialog.github.io/"

_LICENSE = "Apache License 2.0"

_SUBSETS = ("train", "test_freq", "test_rare", "valid_freq", "valid_rare")

_BASE_DATA_URL = "https://huggingface.co/datasets/IVLLab/MultiDialog/resolve/main/"

_AUDIO_ARCHIVE_URL = _BASE_DATA_URL + "data/{subset}/{subset}_chunks_{archive_id:04}.tar.gz"

_META_URL = _BASE_DATA_URL + "metadata/{subset}/{subset}_metadata_{archive_id:04}.jsonl"

logger = datasets.utils.logging.get_logger(__name__)


class MultidialogConfig(datasets.BuilderConfig):
    """BuilderConfig for Multidialog."""

    def __init__(self, name, *args, **kwargs):
        """BuilderConfig for Multidialog
        """
        super().__init__(name=name, *args, **kwargs)
        self.subsets_to_download = (name,)


class Multidialog(datasets.GeneratorBasedBuilder):
    """
    """

    VERSION = datasets.Version("1.0.0")

    BUILDER_CONFIGS = [MultidialogConfig(name=subset) for subset in _SUBSETS]

    DEFAULT_WRITER_BATCH_SIZE = 128

    def _info(self):
        features = datasets.Features(
            {
                "file_name": datasets.Value("string"),
                "conv_id": datasets.Value("string"),
                "utterance_id": datasets.Value("float32"),
                "audio": datasets.Audio(sampling_rate=16_000),
                "from": datasets.Value("string"),
                "value": datasets.Value("string"),
                "emotion": datasets.Value("string"),
                "original_full_path": datasets.Value("string"),  # relative path to full audio in original data dirs
            }
        )
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        splits = (self.config.name,)

        n_archives = {
            "train" : [15, 15], 
            "test_freq": [1, 1], 
            "test_rare": [1, 1],
            "valid_freq": [1, 1], 
            "valid_rare": [1, 1], 
        }

        # 2. prepare sharded archives with audio files
        audio_archives_urls = {
            split: [
                    _AUDIO_ARCHIVE_URL.format(subset=split, archive_id=i)
                    for i in range(n_archives[split][0])
                ]
            for split in splits
        }
        audio_archives_paths = dl_manager.download(audio_archives_urls)
        # flatten archives paths from
        # {"train": {"xs": [path1, path2,], "s": [path3], "m": [path5, path5]}, "dev": {"dev": [path6,...]}, "test": {"test": [...]}}
        # to {"train": [path1, path2, path3, path4, path5], "dev": [path6, ...], "test": [...]}
        # audio_archives_paths = _flatten_nested_dict(audio_archives_paths)
        local_audio_archives_paths = dl_manager.extract(audio_archives_paths) if not dl_manager.is_streaming \
            else None

        # 3. prepare sharded metadata csv files
        meta_urls = {
            split: [
                    _META_URL.format(subset=split, archive_id=i)
                    for i in range(n_archives[split][1])
                ]
            for split in splits
        }
        meta_paths = dl_manager.download_and_extract(meta_urls)
        # meta_paths = _flatten_nested_dict(meta_paths)

        if self.config.name == "test_freq":
            return [
                datasets.SplitGenerator(
                    name="test_freq",
                    gen_kwargs={
                        "audio_archives_iterators": [
                            dl_manager.iter_archive(archive_path) for archive_path in audio_archives_paths["test_freq"]
                        ],
                        "local_audio_archives_paths": local_audio_archives_paths[
                            "test_freq"] if local_audio_archives_paths else None,
                        "meta_paths": meta_paths["test_freq"]
                    },
                ),
            ]
        
        if self.config.name == "test_rare":
            return [
                datasets.SplitGenerator(
                    name="test_rare",
                    gen_kwargs={
                        "audio_archives_iterators": [
                            dl_manager.iter_archive(archive_path) for archive_path in audio_archives_paths["test_rare"]
                        ],
                        "local_audio_archives_paths": local_audio_archives_paths[
                            "test_rare"] if local_audio_archives_paths else None,
                        "meta_paths": meta_paths["test_rare"]
                    },
                ),
            ]    
            
        if self.config.name == "valid_freq":
            return [
                datasets.SplitGenerator(
                    name="valid_freq",
                    gen_kwargs={
                        "audio_archives_iterators": [
                            dl_manager.iter_archive(archive_path) for archive_path in audio_archives_paths["valid_freq"]
                        ],
                        "local_audio_archives_paths": local_audio_archives_paths[
                            "valid_freq"] if local_audio_archives_paths else None,
                        "meta_paths": meta_paths["valid_freq"]
                    },
                ),
            ]    
            
        if self.config.name == "valid_rare":
            return [
                datasets.SplitGenerator(
                    name="valid_rare",
                    gen_kwargs={
                        "audio_archives_iterators": [
                            dl_manager.iter_archive(archive_path) for archive_path in audio_archives_paths["valid_rare"]
                        ],
                        "local_audio_archives_paths": local_audio_archives_paths[
                            "valid_rare"] if local_audio_archives_paths else None,
                        "meta_paths": meta_paths["valid_rare"]
                    },
                ),
            ]   

        if self.config.name == "train":
            return [
                datasets.SplitGenerator(
                    name="train",
                    gen_kwargs={
                        "audio_archives_iterators": [
                            dl_manager.iter_archive(archive_path) for archive_path in audio_archives_paths["train"]
                        ],
                        "local_audio_archives_paths": local_audio_archives_paths[
                            "train"] if local_audio_archives_paths else None,
                        "meta_paths": meta_paths["train"]
                    },
                ),
            ]

    def _generate_examples(self, audio_archives_iterators, local_audio_archives_paths, meta_paths):
        assert len(audio_archives_iterators) == len(meta_paths)
        if local_audio_archives_paths:
            assert len(audio_archives_iterators) == len(local_audio_archives_paths)

        for i, (meta_path, audio_archive_iterator) in enumerate(zip(meta_paths, audio_archives_iterators)):
            meta_dict = dict()
            with open(meta_path) as jsonl_file:
                for line in jsonl_file:
                    data = json.loads(line.strip())
                    meta_dict[data["file_name"]] = data

            for audio_path_in_archive, audio_file in audio_archive_iterator:
                # `audio_path_in_archive` is like "dev_chunks_0000/YOU1000000029_S0000095.wav"
                audio_filename = os.path.split(audio_path_in_archive)[1]
                audio_id = audio_filename.split(".wav")[0]
                audio_meta = meta_dict[audio_path_in_archive]
                audio_meta["conv_id"] = audio_meta.pop("conv_id")
                audio_meta["utterance_id"] = audio_meta.pop("utterance_id")
                audio_meta["from"] = audio_meta.pop("from")
                audio_meta["value"] = audio_meta.pop("value")
                audio_meta["emotion"] = audio_meta.pop("emotion")
                audio_meta["original_full_path"] = audio_meta.pop("audpath")

                path = os.path.join(local_audio_archives_paths[i], audio_path_in_archive) if local_audio_archives_paths \
                    else audio_path_in_archive

                yield audio_id, {
                    "audio": {"path": path , "bytes": audio_file.read()},
                    **{feature: value for feature, value in audio_meta.items() if feature in self.info.features}
                }