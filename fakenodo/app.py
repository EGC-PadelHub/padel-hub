"""
Deprecated entrypoint.

The fakenodo app moved to `app/modules/fakenodo/app.py`.
Run it from the new location:

    python app/modules/fakenodo/app.py

"""

if __name__ == "__main__":
    import sys
    sys.stderr.write(
        "[fakenodo] Moved. Use 'python app/modules/fakenodo/app.py' instead of 'python fakenodo/app.py'\n"
    )
    sys.exit(1)
