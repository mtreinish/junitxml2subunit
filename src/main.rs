extern crate chrono;
extern crate minidom;
extern crate subunit_rust;

use std::env;
use std::fs::File;
use std::io::{self, Read};

use chrono::prelude::*;
use chrono::Duration;
use minidom::Element;
use subunit_rust::Event;

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut buffer = String::new();

    if args.len() >= 2 {
        let path = &args[1];
        let mut f = File::open(path).unwrap();
        let mut buffer = String::new();
        f.read_to_string(&mut buffer);
    } else {
        let stdin = io::stdin();
        let mut handle = stdin.lock();
        handle.read_to_string(&mut buffer);
    }
    let root: Element = buffer.parse().unwrap();

    let mut stdout = io::stdout();
    let mut start_time: DateTime<Utc> = Utc::now();
    for child in root.children() {
        if child.is("testcase", "testrcase") {
            let test_name = child.attr("name");
            let test_class = child.attr("classname");
            let test_status = "success";
            let time = child.attr("time").unwrap().parse::<i64>().unwrap();
            let dur = Duration::seconds(time);
            let mut test_id = "".to_string();
            if test_class.is_some() {
                if test_name.is_some() {
                    test_id = test_class.unwrap().to_owned() + test_name.unwrap();
                } else {
                    test_id = test_class.unwrap().to_string();
                }
            }
            let mut event_start = Event {
                status: Some("inprogress".to_string()),
                test_id: Some(test_id.clone()),
                timestamp: Some(start_time),
                tags: None,
                file_content: None,
                file_name: None,
                mime_type: None,
                route_code: None
            };
            stdout = match event_start.write(stdout) {
                Ok(stdout) => stdout,
                Err(err) => panic!("{}", err),
            };

            let mime_type = None;
            let file_content = None;
            let file_name = None;

            let mut event_stop = Event {
                status: Some(test_status.to_string()),
                test_id: Some(test_id),
                timestamp: Some(start_time + dur),
                tags: None,
                file_content: file_content,
                file_name: file_name,
                mime_type: mime_type,
                route_code: None,
            };

            stdout = match event_stop.write(stdout) {
                Ok(stdout) => stdout,
                Err(err) => panic!("{}", err),
            };

            start_time = start_time + dur;
        }
    }
}
