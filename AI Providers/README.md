# AI Providers

The job of this folder is to provide a common interface for any LLM provider of your choosing for this given task. We will be building a common class where you can import any of your custom classes or one of the pre-built classes of LLM providers so that you can use this project as per your convinience without vendor lock-in.

For simplicity the calls to the LLM providers will not be with stream=True, basically no streaming tokens. The calls to LLMs themselves will be async to optimize the time comsumption as the total lecture + doubt asking might take long.
