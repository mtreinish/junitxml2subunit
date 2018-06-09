junitxml2subunit
================
[![junitxml2subunit on Travis CI][travis-image]][travis]
[![junitxml2subunit on crates.io][cratesio-image]][cratesio]

[travis-image]: https://travis-ci.org/mtreinish/junitxml2subunit.svg?branch=master
[travis]: https://travis-ci.org/mtreinish/junitxml2subunit
[cratesio-image]: https://img.shields.io/crates/v/junitxml2subunit.svg
[cratesio]: https://crates.io/crates/junitxml2subunit

This repo contains a tool for converting junitxml files to the subunit v2
protocol.

## Building

junitxml2subunit is written in Rust, so you'll need to grab a
[Rust installation](https://www.rust-lang.org/)
in order to compile it. Building is easy:

```
$ git clone https://github.com/mtreinish/junitxml2subunit
$ cd junitxml2subunit
$ cargo build --release
```

## Running

Once you've built junitxml2subunit running it is straightforward. The command
takes a single argument the path to the junitxml file to convert. It will then
print the subunit v2 stream for that file to STDOUT. For example:

```
$ junitxml2subunit results.xml
```
