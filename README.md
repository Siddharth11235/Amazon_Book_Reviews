## The Amazon Book Review project

This project is to practice batch-based data pipelines using the[ Amazon Book Reviews dataset](https://jmcauley.ucsd.edu/data/amazon/). I want to practice ingesting data from different sources, in this case a db and an API call. The idea here is as follows:

* Setup a postgres table for the book metadata.
* Setup a datagen API call that send a batch of N (100000 is the value I am using) reviews on being called.
* Setup a job with airflow to process the data to a postgres warehouse.
* Use streamlit to visualize


### Progress
- [x] Setup a postgres table for the book metadata.
- [x] Setup a datagen API call that send a batch of N (100000 is the value I am using) reviews on being called.
- [x] Setup a job with airflow to process the data to a postgres warehouse.
- [x] Use streamlit to visualize basic metrics.
- [x] Split the airflow pipeline into an HTTPS step and a SparkSubmit step.
- [x] Add the word clouds
- [ ] Improve pipeline performance by setting up redis to move data instead of a local folder.
- [ ] Setup terraform to move to cloud if needed.
- [ ] Automate the graphana setup
