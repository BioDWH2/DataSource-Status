# BioDWH2 Data Source Version Status

This repository is a proxy data source version status checker for BioDWH2. As data source version schemas or download
URLs can change at any moment, and adjustments to the data source modules updaters need to be published in a release
version, this checking script is easier and quicker to be adjusted. In an upcoming release, BioDWH2 will be capable of
using the provided versions in this repository in order to make the update process more robust. The checking script is
coupled with a GitHub Action which updates the list regularly.