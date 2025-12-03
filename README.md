# Templates

Template project for working with Field.


## Usage

This project generates a hidden file named `.mkpkg_last`.  
When a new set of templates are generated the `.mkpkg_last` gets the package version written into it.  
This enables new template sets to be generated wihout havin to keep track of the previouse version.  
The previous version is automatically read from `.mkpkg_last` and the next version is then inferred.

### zip-pkg

Generated the next template set.

```shell
python -m mkplg pkg-zip
```

Build version can be overridded using `-b` or `--build`.  
This will generate template set `50` but will NOT upldate `.mkpkg_last`.

```shell
python -m mkplg pkg-zip -b 50
```

The current directory must have the virtual environment activated, `source .venv/bin/activate`, to run the command as python.  
If you have `UV` installed then alternative you can run:

```shell
uv run python -m mkplg pkg-zip
```

This will circumvent the need to activate the virtual environment.