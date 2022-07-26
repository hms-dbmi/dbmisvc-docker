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
