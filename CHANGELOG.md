## [0.7.2](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.7.1...v0.7.2) (2025-07-21)


### Bug Fixes

* **images:** Updated Nginx signing key due to deprecation of the old one ([0f8f08e](https://github.com/hms-dbmi/dbmisvc-docker/commit/0f8f08ea5398f7d4e44628bf045b04fc76a0a009))

## [0.7.1](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.7.0...v0.7.1) (2025-03-27)


### Bug Fixes

* **dependencies:** Updated gunicorn version ([2b50031](https://github.com/hms-dbmi/dbmisvc-docker/commit/2b50031a65331812e2f847538408a05ae224ddba))

# [0.7.0](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.6.2...v0.7.0) (2024-10-23)


### Features

* **init:** Added support for EC2 IMDSv2 ([dc5064b](https://github.com/hms-dbmi/dbmisvc-docker/commit/dc5064bb9125fa0ec6c3afcbc4ccfae8e022b5bb))

## [0.6.2](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.6.1...v0.6.2) (2024-07-09)


### Bug Fixes

* **init:** Only checks for service discovery if enabled ([f3361b9](https://github.com/hms-dbmi/dbmisvc-docker/commit/f3361b96476436ac601fec6f025e3b31aa46c5ce))

## [0.6.1](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.6.0...v0.6.1) (2024-03-21)


### Bug Fixes

* **requirements:** Fixed DockerMake requirement ([48c6888](https://github.com/hms-dbmi/dbmisvc-docker/commit/48c68884771a8c7db8ae9dd1a33874f40396fafb))
* **targets:** Updated build targets; removed deprecated targets; fixed Nginx configuration ([447aaf7](https://github.com/hms-dbmi/dbmisvc-docker/commit/447aaf72c977112d5daffc91a781c0f3099d284d))

# [0.6.0](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.5.1...v0.6.0) (2023-11-14)


### Bug Fixes

* **docker:** Set service discovery listener as unencrypted by default, with option to use a self-signed SSL certificate ([13a949f](https://github.com/hms-dbmi/dbmisvc-docker/commit/13a949fc7aee373c9789778f850de76f052fd4b2))


### Features

* **docker:** Implemented support for service discovery endpoints ([b9ae9e8](https://github.com/hms-dbmi/dbmisvc-docker/commit/b9ae9e80beb778e9cebcd0f2be053e22978f4ac2))

## [0.5.1](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.5.0...v0.5.1) (2023-07-17)


### Bug Fixes

* **docker:** Installes 'less' package on all images ([6b11702](https://github.com/hms-dbmi/dbmisvc-docker/commit/6b11702688752cf173256324b764dfe861aa131a))
* **docker:** Moved awscli from Python dependencies to binary installation ([b84a5c2](https://github.com/hms-dbmi/dbmisvc-docker/commit/b84a5c2a1abc459616d9dc195ae5e8b6745d1eba))

# [0.5.0](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.4.0...v0.5.0) (2022-07-19)


### Features

* **network:** Updated to configure networking for Fargate tasks ([758c658](https://github.com/hms-dbmi/dbmisvc-docker/commit/758c658f7e1ab73108ac33bbff615c53728f6c6d))

# [0.4.0](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.3.3...v0.4.0) (2022-06-11)


### Features

* **security:** Set Debian-based images to install security patches ([0e548d4](https://github.com/hms-dbmi/dbmisvc-docker/commit/0e548d4b1cd1631e7b8a273be4b26d7329168306))

## [0.3.3](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.3.2...v0.3.3) (2022-04-28)


### Bug Fixes

* **requirements:** Image requirements update ([a231304](https://github.com/hms-dbmi/dbmisvc-docker/commit/a231304d3c463f1ff7d71b6deb294022588cb207))

## [0.3.2](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.3.1...v0.3.2) (2022-03-17)


### Bug Fixes

* **build:** DBMISVC-113 - Some Ubuntu codenames are without spaces so regex had to be updated accordingly ([b4e0116](https://github.com/hms-dbmi/dbmisvc-docker/commit/b4e0116133f6135948a7f3a5b59017c82a6d028a))
* **targets:** DBMISVC-113 - Added older but still LTS Ubuntu targets ([6a97407](https://github.com/hms-dbmi/dbmisvc-docker/commit/6a97407af09366908f458fa3ce7c6838d3a0c4ec))

## [0.3.1](https://github.com/hms-dbmi/dbmisvc-docker/compare/v0.3.0...v0.3.1) (2022-03-17)


### Bug Fixes

* **nginx:** DBMISVC-111/112 - Fixes file proxy DNS resolution in private networks; fixes Nginx restart bug; refactored some Nginx configuration steps ([ddab01c](https://github.com/hms-dbmi/dbmisvc-docker/commit/ddab01c772582c51f5609ed0a927a229971676e4))

# 0.3.0 (2022-02-15)


### Bug Fixes

* **builds:** Refactored build steps; implemented fully configurable Nginx installs ([d2a6d53](https://github.com/hms-dbmi/dbmisvc-docker/commit/d2a6d533ddc52f64763fe5f6906b553244ec31a5))
* **builds:** Refactored Nginx builds ([badb2e9](https://github.com/hms-dbmi/dbmisvc-docker/commit/badb2e9e22f1c1e2a4fdaa0794c7cfd0a1fba4ac))
* **debian:** Fixed Debian version argument naming ([14173c5](https://github.com/hms-dbmi/dbmisvc-docker/commit/14173c50916f6a16c7d767717f2949006b9d94ae))
* **dependencies:** Bumped versions of AWS CLI and Gunicorn ([a76748f](https://github.com/hms-dbmi/dbmisvc-docker/commit/a76748f81a3754f5b62a974ac55c101f72ef7764))
* **docker:** Moved Python dependencies from image to pip-tools managed requirements file; added Github action to automate builds ([b5dfbe1](https://github.com/hms-dbmi/dbmisvc-docker/commit/b5dfbe198ba68b5b715fe401e2aeea5bd4d98ca5))
* **docker:** Removed tabs from Debian build file ([a5d493d](https://github.com/hms-dbmi/dbmisvc-docker/commit/a5d493dcec3ab9343ffb6ce9f5f59a0aef87f04b))
* **init:** Reverted to using AWS IMDSv1 due to issues fetching ALB IP ([b6225cc](https://github.com/hms-dbmi/dbmisvc-docker/commit/b6225cc30b8c79517a0ba20c9ede567f43e05487))
* **targets:** Removed '-zip' targets; added dynamic modules for Nginx ([1b1a0fe](https://github.com/hms-dbmi/dbmisvc-docker/commit/1b1a0fe8a64fe28e0102278a798bd5ac1bfa2af4))
* **ubuntu:** Fixed Ubuntu Python and Nginx steps ([e384dc7](https://github.com/hms-dbmi/dbmisvc-docker/commit/e384dc7aaf8e3d482fd793b351439e9f1f18c273))


### Features

* **targets:** Bumped target defaults and removed unsupported target versions ([e5d72ee](https://github.com/hms-dbmi/dbmisvc-docker/commit/e5d72eeb25b9f55454e8900a2d42fc56b8249203))
