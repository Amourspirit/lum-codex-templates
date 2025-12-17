# Templates

Template project for working with Field.


## Usage

This project generates a hidden file named `.mkpkg_last`.  
When a new set of templates are generated the `.mkpkg_last` gets the package version written into it.  
This enables new template sets to be generated wihout having to keep track of the previous version.  
The previous version is automatically read from `.mkpkg_last` and the next version is then inferred.

### zip-pkg

Generated the next template set.

```shell
python -m mkplg pkg-zip
```

Build version can be overrode using `-b` or `--build`.  
This will generate template set `50` but will NOT update `.mkpkg_last`.

```shell
python -m mkplg pkg-zip -b 50
```

The current directory must have the virtual environment activated, `source .venv/bin/activate`, to run the command as python.  
If you have `UV` installed then alternative you can run:

```shell
uv run python -m mkplg pkg-zip
```

This will circumvent the need to activate the virtual environment.

## MMR-000-GLOBAL

The `MMR-000-GLOBAL` is in file `Metadata/00-Master_Metadata_Registry.yml`.  
When the file is manually updated `version` should be bumped such as `3.3` to `3.4`.  
However, the `version` should always be a two digit (major, minor) version and not a three digit version.  
The reason for this is when the package is built the revision is the build number.  
So, if the version is `3.4` and the package build number is `88` then final outputted version will becomes `3.4.88`.  
This is done because each build modifies the outputted `00-Master_Metadata_Registry.yml` file so it must have a version to reflect that a change as occurred.

## Updating Templates

### Updating Template

Templates `id`, `version`,`category`, and `name` values are set in `pyproject.toml` file under `tool.project.templates.TEMPLATE_TYPE` sections.

### Metadata Templates

Each template has a corresponding metadata for managing its field matrix.  
When a template has its metadata modified it must also be reflected in it corresponding metadata template.  
The metadata for templates is found in `Metadata/templates`.
