
use std::path::{Path, PathBuf};

use tch::{Tensor, Kind, Device, nn, Cuda, no_grad};

use rust_sentence_transformers::model::SentenceTransformer;

fn main() -> failure::Fallible<()> {

    let device = Device::Cpu;
    let sentences = [
        "Bushnell is located at 40°33′6″N 90°30′29″W (40.551667, -90.507921).",
        "According to the 2010 census, Bushnell has a total area of 2.138 square miles (5.54 km2), of which 2.13 square miles (5.52 km2) (or 99.63%) is land and 0.008 square miles (0.02 km2) (or 0.37%) is water.",
        "The town was founded in 1854 when the Northern Cross Railroad built a line through the area.",
        "Nehemiah Bushnell was the President of the Railroad, and townspeople honored him by naming their community after him.",
        "Bushnell was also served by the Toledo, Peoria and Western Railway, now the Keokuk Junction Railway.",
        "As of the census[6] of 2000, there were 3,221 people, 1,323 households, and 889 families residing in the city.",
    ];

    let embedder = SentenceTransformer::new(
        Path::new("/Users/flippchen/.cache/huggingface/hub/models--sentence-transformers--msmarco-distilbert-base-v4"),
        device)?;

    let embedings = &embedder.encode(sentences.to_vec(), Some(8));
    println!("{:?}", embedings);
    Ok(())
}