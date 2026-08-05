#!/usr/bin/env python

import argparse
import pathlib
import itertools
import sys
import typing
import json
import operator

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


def run(
    input_dir: pathlib.Path,
    output_dir: pathlib.Path,
    config_path: pathlib.Path,
    name: str,
) -> None:

    if not input_dir.is_dir():
        msg = f"Input directory '{input_dir}' does not exist"
        raise ValueError(msg)

    if not output_dir.is_dir():
        if output_dir.exists():
            msg = f"Output directory '{output_dir}' exists but is not a directory"
            raise ValueError(msg)
        msg = f"Output directory '{output_dir}' does not exist; creating"
        output_dir.mkdir(parents=True)

    image_paths = get_image_paths(image_dir=input_dir)

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
        image_paths=image_paths,
        output_paths=output_paths,
        config_path=config_path,
    )

    doc = Metashape.Document()

    chunk = doc.addChunk()

    for step in STEPS:

        step_params = config.pop(step, {})

        print(f"Running step '{step}' with params '{step_params}'", flush=True)

        assert hasattr(chunk, step)

        func = getattr(chunk, step)

        func(**step_params)

        print(f"Finished '{step}'" + "\n" + "-" * 10, flush=True)

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

    for (step_key, step_value) in config.items():

        if step_key not in STEPS:
            msg = f"Unexpected key in configuration: '{step_key}'"
            raise ValueError(msg)

        overrides = []

        for (key, value) in step_value.items():

            if isinstance(value, str) and value.startswith("Metashape."):

                (_, *enum_path) = value.split(".")

                enum_value = operator.attrgetter(".".join(enum_path))(Metashape)

                overrides.append((step_key, key, enum_value))

    for (step_key, key, value) in overrides:
        config[step_key][key] = value

    return config


def form_config(
    image_paths: tuple[str, ...],
    output_paths: dict[str, str],
    config_path: pathlib.Path | None,
) -> dict[str, typing.Any]:

    pre_config = {
        "exportModel": {
            "save_metadata_xml": True,
        },
    }

    user_config = load_config(config_path=config_path)

    post_config = {
        "addPhotos": {
            "filenames": image_paths,
        },
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
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input-dir",
        required=True,
        type=pathlib.Path,
        help="Directory containing the images to use as input.",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=pathlib.Path,
        help="Directory to write the pipeline output.",
    )

    parser.add_argument(
        "--config-path",
        required=False,
        default=None,
        type=pathlib.Path,
        help="Path to a JSON file containing execution parameters.",
    )

    parser.add_argument(
        "--name",
        required=False,
        type=str,
        default="mesh",
        help="Base name to use for output files.",
    )

    args = parser.parse_args()

    run(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        config_path=args.config_path,
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
