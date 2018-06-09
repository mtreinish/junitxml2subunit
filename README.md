Subunit Rust
============

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
