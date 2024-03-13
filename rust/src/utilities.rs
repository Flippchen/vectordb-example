use rust_bert::pipelines::sentence_embeddings::{
    SentenceEmbeddingsBuilder,
};

pub fn get_embeddings(titles: &[String], model_path: String) -> Vec<Vec<f32>> {
    let model = SentenceEmbeddingsBuilder::local(model_path)
        .with_device(tch::Device::cuda_if_available())
        .create_model().unwrap();

    // Generate Embeddings
    let embeddings = model.encode(&titles).unwrap();
    embeddings
}