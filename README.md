# Rewind

![Badge for GitHub repo top language](https://img.shields.io/github/languages/top/legionxvx/rewind?style=flat&logo=appveyor) ![Badge for GitHub last commit](https://img.shields.io/github/last-commit/legionxvx/rewind?style=flat&logo=appveyor)

Check out the badges hosted by [shields.io](https://shields.io/).


## Description 

Rewind is a wrapper around the Streamlink project to allow for custom plugins that are 'rerun' aware (like Twitch VODs)

Currently supported plugins

## Table of Contents
* [Installation](#installation)
* [Usage](#usage)
* [Contributing](#contributing)
* [Tests](#tests)
* [License](#license)

# Installation

## Easiest Method (Not Intending Development)
```bash
$ pip install rewind
```

## For Everyone Else
```bash
$ git checkout ...
$ cd repo
$ poetry install
$ poetry run python -m rewind
```

# Usage

```bash
$ rewind www.twitch.tv/clinststevens best --twitch-check-vods
```

# Tests

*Tests for application and how to run them:*

poetry run pytest

# License

GNU GPLv3

## Questions?

![Developer Profile Picture](https://avatars.githubusercontent.com/u/38223208?v=4) 

For any questions, please contact me with the information below:

GitHub: [@legionxvx](https://api.github.com/users/legionxvx)