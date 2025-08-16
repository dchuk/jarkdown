# Documentation

This directory contains all documentation for the jarkdown project.

## Structure

- **`source/`** - Source files for the official documentation (Sphinx/ReadTheDocs)
- **`design/`** - Internal design documents, PRDs, and architectural decisions

## Building Documentation

Documentation will be built using Sphinx and can be published to ReadTheDocs.

To build the documentation locally (once configured):

```bash
cd docs/
make html
```

The built documentation will be available in `docs/_build/html/`.
