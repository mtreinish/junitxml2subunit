// Copyright 2018 Matthew Treinish
//
// This file is part of junitxml2subunit
//
// junitxml2subunit is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// junitxml2subunit is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with junitxml2subunit.  If not, see <http://www.gnu.org/licenses/>.

extern crate chrono;
extern crate num_traits;
extern crate quick_xml;
extern crate subunit_rust;

use std::env;
use std::error::Error;
use std::io::{self, Write};
use std::path::Path;
use std::process;
use std::str;

use chrono::prelude::*;
use chrono::Duration;
use num_traits::pow;
use quick_xml::events::Event as XMLEvent;
use quick_xml::Reader;
use subunit_rust::Event;

type GenError = Box<Error>;
type GenResult<T> = Result<T, GenError>;

fn write_first_packet<T: Write>(
    test_id: &String,
    timestamp: DateTime<Utc>,
    output: T,
) -> GenResult<T> {
    let mut event_start = Event {
        status: Some("inprogress".to_string()),
        test_id: Some(test_id.to_string()),
        timestamp: Some(timestamp),
        tags: None,
        file_content: None,
        file_name: None,
        mime_type: None,
        route_code: None,
    };
    let result = event_start.write(output)?;
    return Result::Ok(result);
}

fn write_second_packet<T: Write>(
    status: &String,
    test_id: &String,
    timestamp: DateTime<Utc>,
    file_content: Option<Vec<u8>>,
    file_name: Option<String>,
    mime_type: Option<String>,
    output: T,
) -> GenResult<T> {
    let mut event_stop = Event {
        status: Some(status.to_string()),
        test_id: Some(test_id.to_string()),
        timestamp: Some(timestamp),
        tags: None,
        file_content: file_content,
        file_name: file_name,
        mime_type: mime_type,
        route_code: None,
    };
    let result = event_stop.write(output)?;
    return Result::Ok(result);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut reader;
    if args.len() >= 2 {
        let path = Path::new(&args[1]);
        reader = Reader::from_file(path).unwrap();
        reader.trim_text(true);
    } else {
        eprintln!("You need to pass a xml file in as the first argument");
        process::exit(1);
    }

    let mut stdout = io::stdout();
    let mut start_time: DateTime<Utc> = Utc::now();
    let mut buf = Vec::new();
    let mut test_id = "".to_string();
    let mut success_attachment: Option<String> = None;
    let mut stop_time: DateTime<Utc> = Utc::now();
    loop {
        match reader.read_event(&mut buf) {
            Ok(XMLEvent::Start(ref e)) => {
                if e.name() == "testcase".as_bytes() {
                    if test_id != "".to_string() {
                        let status = "success".to_string();
                        if success_attachment.is_some() {
                            let fname = "stdout".to_string();
                            let mime = "text/plain".to_string();
                            stdout = write_second_packet(
                                &status,
                                &test_id,
                                stop_time,
                                Some(success_attachment.unwrap().into_bytes()),
                                Some(fname),
                                Some(mime),
                                stdout,
                            ).unwrap();
                        } else {
                            stdout = write_second_packet(
                                &status, &test_id, stop_time, None, None, None, stdout,
                            ).unwrap();
                        }
                        success_attachment = None;
                    }
                    let mut class_name = None;
                    let mut time = None;
                    let mut test_name = None;
                    for attribute in e.attributes() {
                        let attr = attribute.unwrap();
                        if attr.key == "name".as_bytes() {
                            test_name = Some(attr.value);
                        } else if attr.key == "classname".as_bytes() {
                            class_name = Some(attr.value);
                        } else if attr.key == "time".as_bytes() {
                            time = Some(attr.value);
                        }
                    }
                    if !time.is_some() {
                        eprintln!("Invalid XML: There is no time attribute on a testcase");
                        process::exit(2);
                    } else {
                        let mut time_cow = time.unwrap();
                        let time_str = str::from_utf8(time_cow.to_mut()).unwrap();
                        let time_64 = time_str.parse::<f64>().unwrap();
                        let time_nano = time_64 * pow(10f64, 9);
                        let dur = Duration::nanoseconds(time_nano as i64);
                        stop_time = start_time + dur;
                    }
                    if !test_name.is_some() && !class_name.is_some() {
                        eprintln!("Invalid XML: There is no testname or classname attribute on a testcase");
                        process::exit(3);
                    }
                    if class_name.is_some() {
                        if test_name.is_some() {
                            test_id = str::from_utf8(class_name.unwrap().to_mut())
                                .unwrap()
                                .to_owned()
                                + str::from_utf8(test_name.unwrap().to_mut()).unwrap();
                        } else {
                            test_id = str::from_utf8(test_name.unwrap().to_mut())
                                .unwrap()
                                .to_string();
                        }
                    }
                    stdout = write_first_packet(&test_id, start_time, stdout).unwrap();
                    start_time = stop_time;
                } else if e.name() == "skipped".as_bytes() {
                    let mut message = false;
                    let status = "skip".to_string();
                    for attribute in e.attributes() {
                        let attr = attribute.unwrap();
                        if attr.key == "message".as_bytes() {
                            let file_content = attr.value;
                            let fname = "reason".to_string();
                            let mime = "text/plain".to_string();
                            stdout = write_second_packet(
                                &status,
                                &test_id,
                                stop_time,
                                Some(file_content.to_vec()),
                                Some(fname),
                                Some(mime),
                                stdout,
                            ).unwrap();
                            message = true;
                            break;
                        }
                    }
                    if !message {
                        stdout = write_second_packet(
                            &status, &test_id, stop_time, None, None, None, stdout,
                        ).unwrap();
                    }
                    test_id == "".to_string();
                } else if e.name() == "failure".as_bytes() {
                    let mut message = false;
                    let status = "fail".to_string();
                    for attribute in e.attributes() {
                        let attr = attribute.unwrap();
                        if attr.key == "message".as_bytes() {
                            let file_content = attr.value;
                            let fname = "traceback".to_string();
                            let mime = "text/plain".to_string();

                            stdout = write_second_packet(
                                &status,
                                &test_id,
                                stop_time,
                                Some(file_content.to_vec()),
                                Some(fname),
                                Some(mime),
                                stdout,
                            ).unwrap();
                            message = true;
                            break;
                        }
                    }
                    if !message {
                        stdout = write_second_packet(
                            &status, &test_id, stop_time, None, None, None, stdout,
                        ).unwrap();
                    }
                    test_id = "".to_string();
                }
                let mut test_id = "".to_string();
            }
            Ok(XMLEvent::Eof) => {
                let status = "success".to_string();
                write_second_packet(&status, &test_id, stop_time, None, None, None, stdout)
                    .unwrap();
                break;
            }
            Err(e) => panic!("Error at position {}: {:?}", reader.buffer_position(), e),
            Ok(XMLEvent::Text(e)) => {
                if test_id != "".to_string() {
                    let attach = e.unescape_and_decode(&reader).unwrap();
                    if !attach.is_empty() {
                        success_attachment = Some(attach);
                    }
                }
            }
            _ => (),
        }
        buf.clear()
    }
}
