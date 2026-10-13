#!/usr/bin/env python

import argparse
import dataclasses
import datetime
import itertools
import json
import operator
import pathlib
import pprint
import sys
import typing

import Metashape


STEPS = (
    "addPhotos",
    "matchPhotos",
    "alignCameras",
    "buildDepthMaps",
    "buildModel",
    "buildUV",
    "buildTexture",
    "exportModel",
    "exportReport",
)


@dataclasses.dataclass
class Param:
    function: str
    param: str
    value: str | int
    arg: str | int | None = None

    def __post_init__(self) -> None:

        if self.arg is None:
            self.arg = self.value


@dataclasses.dataclass
class ParamSet:
    match_photos: Param
    build_depth_maps: Param
    build_model: Param
    build_uv: Param
    build_texture: Param

    def __str__(self) -> str:
        return "__".join(
            str(getattr(self, field.name))
            for field in dataclasses.fields(self)
        )

    def as_config_dict(self) -> dict[str, dict[str, str | int]]:

        config: dict[str, dict[str, str | int]] = {}

        for field in dataclasses.fields(self):

            param = getattr(self, field.name)

            func_config: dict[str, str | int] = config.get(param.function, {})

            func_config[param.param] = param.arg

            config[param.function] = func_config

        return config


PRESETS = {
    "medium": ParamSet(
        match_photos=Param(
            function="matchPhotos",
            param="downscale",
            value=1,
        ),
        build_depth_maps=Param(
            function="buildDepthMaps",
            param="downscale",
            value=16,
        ),
        build_model=Param(
            function="buildModel",
            param="face_count",
            arg="Metashape.FaceCount.MediumFaceCount",
            value="Medium",
        ),
        build_uv=Param(
            function="buildUV",
            param="texture_size",
            value=8192,
        ),
        build_texture=Param(
            function="buildTexture",
            param="texture_size",
            value=8192,
        ),
    ),
    "high": ParamSet(
        match_photos=Param(
            function="matchPhotos",
            param="downscale",
            value=1,
        ),
        build_depth_maps=Param(
            function="buildDepthMaps",
            param="downscale",
            value=8,
        ),
        build_model=Param(
            function="buildModel",
            param="face_count",
            arg="Metashape.FaceCount.MediumFaceCount",
            value="Medium",
        ),
        build_uv=Param(
            function="buildUV",
            param="texture_size",
            value=8192,
        ),
        build_texture=Param(
            function="buildTexture",
            param="texture_size",
            value=8192,
        ),
    ),
    "highest": ParamSet(
        match_photos=Param(
            function="matchPhotos",
            param="downscale",
            value=1,
        ),
        build_depth_maps=Param(
            function="buildDepthMaps",
            param="downscale",
            value=4,
        ),
        build_model=Param(
            function="buildModel",
            param="face_count",
            arg="Metashape.FaceCount.MediumFaceCount",
            value="Medium",
        ),
        build_uv=Param(
            function="buildUV",
            param="texture_size",
            value=8192,
        ),
        build_texture=Param(
            function="buildTexture",
            param="texture_size",
            value=8192,
        ),
    ),
}


def run(
    output_dir: pathlib.Path,
    input_dir: pathlib.Path | None,
    config_path: pathlib.Path | None,
    preset: str | None,
    name: str,
) -> None:

    if input_dir is not None and not input_dir.is_dir():
            msg = f"Input directory '{input_dir}' does not exist"
            raise ValueError(msg)

    if input_dir is None and config_path is None:
        msg = (
            "A configuration file must be provided if `input_dir` is not "
            "specified."
        )
        raise ValueError(msg)

    if not output_dir.is_dir():
        if output_dir.exists():
            msg = f"Output directory '{output_dir}' exists but is not a directory"
            raise ValueError(msg)
        msg = f"Output directory '{output_dir}' does not exist; creating"
        output_dir.mkdir(parents=True)

    output_paths: dict[str, str] = {}

    for (component, ext) in (
        ("model", "glb"),
        ("report", "pdf"),
        ("doc", "psz"),
    ):

        component_path = str(output_dir / f"{name}.{ext}")

        # metashape requires that paths always contain a directory structure
        # so something like 'mesh.glb' in the working directory will give an error
        # we need to replace it by './mesh.glb' in that instance
        if output_dir == pathlib.Path("."):
            component_path = f"./{component_path}"

        output_paths[component] = component_path

    config = form_config(
        input_dir=input_dir,
        output_paths=output_paths,
        config_path=config_path,
        preset=preset,
    )

    print("Using configuration:")
    pprint.pprint(config)
    print("-" * 10)

    doc = Metashape.Document()

    chunk = doc.addChunk()

    for step in STEPS:

        step_params = config.pop(step, {})

        print(
            (
                f"{datetime.datetime.now()} :: "
                f"Running step '{step}' with params '{step_params}'"
            ),
            flush=True,
        )

        assert hasattr(chunk, step)

        func = getattr(chunk, step)

        func(**step_params)

        print(
            (
                f"{datetime.datetime.now()} :: "
                f"Finished '{step}'" + "\n" + "-" * 10
            ),
            flush=True,
        )

    doc.save(path=output_paths["doc"])

    print(f"Saved Metashape file to '{output_paths['doc']}'", flush=True)

    sys.exit(0)


def load_config(config_path: pathlib.Path | None) -> dict[str, typing.Any]:

    config: dict[str, typing.Any]

    if config_path is None:
        return {}

    raw_config = config_path.read_text()

    if not raw_config:
        return {}

    full_config = json.loads(raw_config)

    config = full_config.get("pg_settings", None)

    if config is None:
        return {}

    overrides = []

    for (step_key, step_value) in config.items():

        if step_key not in STEPS:
            msg = f"Unexpected key in configuration: '{step_key}'"
            raise ValueError(msg)

        for (key, value) in step_value.items():

            if isinstance(value, str) and value.startswith("Metashape."):

                (_, *enum_path) = value.split(".")

                enum_value = operator.attrgetter(".".join(enum_path))(Metashape)

                overrides.append((step_key, key, enum_value))

    for (step_key, key, value) in overrides:
        config[step_key][key] = value

    return config


def form_config(
    input_dir: pathlib.Path | None,
    output_paths: dict[str, str],
    config_path: pathlib.Path | None,
    preset: str | None,
) -> dict[str, typing.Any]:

    pre_config = {
        "buildModel": {
            "vertex_colors": False,
            "build_texture": False,
        },
        "buildTexture": {
            # it crashes without this
            "blending_mode": Metashape.BlendingMode.MosaicBlending,
        },
        "exportModel": {
            "save_metadata_xml": True,
        },
    }

    preset_config = (
        PRESETS[preset].as_config_dict()
        if preset is not None
        else {}
    )

    user_config = load_config(config_path=config_path)

    if input_dir is None:

        if (
            "addPhotos" not in user_config
            or "filenames" not in user_config["addPhotos"]
        ):
            msg = (
                "If `input_dir` is not provided, the specific image paths must be "
                "specified in the JSON configuration under the 'filenames' key of the "
                "'addPhotos' key."
            )
            raise ValueError(msg)

        # all good, ["addPhotos"]["filenames"] is in the config

    else:

        # provided both
        # could potentially combine them, but better to be careful and raise an error
        if (
            "addPhotos" in user_config
            and "filenames" in user_config["addPhotos"]
        ):
            msg = (
                "Both `input_dir` and specific filenames in the configuration have "
                "been provided. To avoid ambiguity, please specify one or the other."
            )
            raise ValueError(msg)

        # figure out the paths to include
        image_paths = get_image_paths(image_dir=input_dir)

        if "addPhotos" not in user_config:
            user_config["addPhotos"] = {}

        user_config["addPhotos"]["filenames"] = image_paths

    post_config = {
        "exportModel": {
            "path": output_paths["model"],
        },
        "exportReport": {
            "path": output_paths["report"],
        },
    }

    config = {
        step: (
            pre_config.get(step, {})
            | preset_config.get(step, {})
            | user_config.get(step, {})
            | post_config.get(step, {})
        )
        for step in STEPS
    }

    return config


def get_image_paths(image_dir: pathlib.Path) -> tuple[str, ...]:

    # those supported by metashape
    image_extensions = (
        "jpg", "jpeg",
        "jp2", "j2k",
        "jxl",
        "tif", "tiff",
        "dng",
        "png",
        "exr",
        "bmp",
        "tga",
        "pgm", "ppm",
        "seq",
        "ara",
        "mpo",
    )

    image_paths = tuple(
        itertools.chain(
            str(path)
            for ext in image_extensions
            for path in image_dir.glob(f"*.{ext}", case_sensitive=False)
        )
    )

    if len(image_paths) == 0:
        msg = f"No valid images found in '{image_dir}'"
        raise ValueError(msg)

    return image_paths


def cli() -> None:

    parser = argparse.ArgumentParser(
        description="Runs the Metashape photogrammetry pipeline.",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=pathlib.Path,
        help="Directory to write the pipeline output.",
    )

    parser.add_argument(
        "--input-dir",
        required=False,
        type=pathlib.Path,
        help=(
            "(Optional) Directory containing the images to use as input. "
            "If not provided, the specific image paths must be specified "
            "in the JSON configuration under the 'filenames' key of the "
            "'addPhotos' key."
        ),
    )

    parser.add_argument(
        "--config-path",
        required=False,
        default=None,
        type=pathlib.Path,
        help="(Optional) Path to a JSON file containing execution parameters.",
    )

    parser.add_argument(
        "--preset",
        required=False,
        default=None,
        choices=list(PRESETS),
        help="(Optional) Use a set of pre-defined configuration parameters.",
    )

    parser.add_argument(
        "--name",
        required=False,
        type=str,
        default="mesh",
        help="(Optional) Base name to use for output files. (default='mesh')",
    )

    args = parser.parse_args()

    run(
        output_dir=args.output_dir,
        input_dir=args.input_dir,
        config_path=args.config_path,
        preset=args.preset,
        name=args.name,
    )


if __name__ == "__main__":

    if not Metashape.app.activated:
        msg = (
            "The `Metashape` application is not activated; use the `AGISOFT_FLS` "
            + "environment variable to set the license server"
        )
        raise ValueError(msg)

    cli()
