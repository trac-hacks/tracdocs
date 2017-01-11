# TracDocs

The TracDocs project is a plugin for the [trac](https://trac.edgewall.org/)
project management tool.

Many documents exists adjacent to the code that is being developed and
managed. These documents are not conveniently stored in a wiki due to the lack
of offline access and editing. Also, a wiki tends to be less structured than
the documentation that lives with source code.

The TracDocs plugin adds a "Docs" tab to the trac project. Underneath this
tab can be found all of the documentation that the current logged in user has
access to.

Some features:

* Uses [RestructuredText](http://docutils.sourceforge.net/rst.html) as a
  markup language.

* Supports inline images and links.

* Highlights source code using google-code-prettify.

* Supports editing through Subversion and the Trac website.

* Handles user permission using Subversion authorization.

* Supports downloading binaries with proper mime-types for non-text files.

Note: this plugin respects the access rights of the user that is logged in.


## Installation

The TracDocs plugin can be installed using standard:

```
$ pip install tracdocs
```

Or, grab the sources and build using:

```
$ python setup.py install
```

## Configuration

It is configured in the ``trac.ini`` file by enabling the component and
configuring the path within the Subversion repository to store the wiki
documents:

```ini
[components]
tracdocs.* = enabled

[docs]
root = wiki/trunk
```

By default, it will show the title of the directory that you are navigating,
but if you create an ``index.txt`` file in the directory, it will use that
instead, allowing you to put additional documentation at the top of a
directory structure.

It uses the ``WIKI_VIEW`` permissions to control access to the documentation
pages.
