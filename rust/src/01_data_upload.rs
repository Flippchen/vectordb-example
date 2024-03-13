extern crate tokio;
extern crate redis;
extern crate csv;
extern crate serde;
extern crate dotenv;
extern crate postgres;
extern crate rust_decimal;


use std::{env, fs::File, error::Error};
use serde::{Serialize, Deserialize};
use csv::ReaderBuilder;
use postgres::{Client, NoTls, Row};
use dotenv::dotenv;

#[derive(Debug, Serialize, Deserialize)]
struct Movie {
    title: String,
    overview: String,
    budget: rust_decimal::Decimal,
    revenue: rust_decimal::Decimal,
    runtime: i32,
}

fn read_or_fetch_movies() -> Result<Vec<Movie>, Box<dyn Error>> {
    dotenv().ok();
    let file_path = "all_movies.csv";
    let db_params = format!(
        "host={} user={} password={} dbname={} port={}",
        env::var("POSTGRES_HOST").expect("DB_HOST must be set"),
        env::var("POSTGRES_USER").expect("DB_USER must be set"),
        env::var("POSTGRES_PASSWORD").expect("DB_PASS must be set"),
        env::var("dbname").expect("DB_NAME must be set"),
        env::var("POSTGRES_PORT").expect("DB_PORT must be set")
    );

    if std::path::Path::new(file_path).exists() {
        let mut rdr = ReaderBuilder::new()
            .has_headers(true)
            .from_path(file_path)?;
        let mut movies = vec![];
        for result in rdr.deserialize() {
            let record: Movie = result?;
            movies.push(record);
        }
        Ok(movies)
    } else {
        let mut client = Client::connect(&db_params, NoTls)?;
        let rows = client.query("
            SELECT title, overview, budget, revenue, runtime
            FROM movies
            WHERE budget > 0 AND revenue > 0 AND runtime > 0 AND title IS NOT NULL AND overview IS NOT NULL
            ", &[])?;

        let movies: Vec<Movie> = rows.into_iter()
            .map(|row| Movie {
                title: row.get(0),
                overview: row.get(1),
                budget: row.get(2),
                revenue: row.get(3),
                runtime: row.get(4),
            })
            .collect();

        let mut wtr = csv::Writer::from_path(file_path)?;
        for movie in &movies {
            wtr.serialize(movie)?;
        }
        wtr.flush()?;
        Ok(movies)
    }
}
fn upload_to_redis(movies: Vec<Movie>) -> redis::RedisResult<()> {
    let client = redis::Client::open("redis://127.0.0.1/").unwrap();
    let mut con = client.get_connection().unwrap();

    let mut pipeline = redis::pipe();
    for (i, movie) in movies.iter().enumerate() {
        let redis_key = format!("movies:{:03}", i);
        let movie_json = serde_json::to_string(&movie).unwrap();
        pipeline.cmd("JSON.SET").arg(&redis_key).arg("$").arg(movie_json).ignore();
    }
    pipeline.execute(&mut con);
    Ok(())
}


fn main() -> Result<(), Box<dyn Error>> {
    let movies = read_or_fetch_movies()?;
    upload_to_redis(movies)?;
    Ok(())
}