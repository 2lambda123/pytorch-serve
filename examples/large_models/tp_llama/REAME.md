# Loading large Huggingface models with constrained resources using accelerate

This document briefs on serving the [Llama 2](https://huggingface.co/meta-llama) as presented in the original [Llama repo](https://github.com/facebookresearch/llama/tree/main) using PyTorch(PT) Tensor Parallel (TP) APIs, which under the hood make use of DTensors. It basically, take a sharding plan for linear layers in MLP and Attention blocks of Llama2 model and just simply wrap the model given the sharding plan. In the following, we show the steps how to serve the Llama2 7-70B  model with Torchserve.

Here we convert the Meta Llama model, which is based on Fairscale TP layers to PT distributed compliant checkpoints and use PT TP (DTensor) API to run the Distributed inference.

**Note** The following has been tested on A100 GPUs with 40 GB memory so far.


### How to use it?


1- Make sure you have access to llama weights on [HF model hub](https://huggingface.co/meta-llama), there is form you need to fill up and within few mins you will get access. ANy model name on the hub **without -hf** is Meta/FAIR weight.

Make sure you you are signed up in HF as well, you will need you API token than can be access from [here](https://huggingface.co/settings/tokens), note to use the same email for accessing the weights as email you signed in to HF.

Once you have the access, in your terminal login to HF

```
huggingface-cli login YOUR_TOKEN

```

### Step 1: Install requirements

Make sure to have PyTorch Nighlies installed.

```
pip3 install --pre torch  --index-url https://download.pytorch.org/whl/nightly/cu118

pip install transformers 

```

### Step 2: Download model

Login into HuggingFace hub with token by running the below command, **make sure to specify the right name for the model from [HuggingFace (HF) model hub](https://huggingface.co/meta-llama), any model name on the model hub without -hf is Meta original model/ checkpoints and we need them not the HF converted versions.**



```bash
huggingface-cli login
```
paste the token generated from HuggingFace hub. Make sure `use_auth_token=True` is in [Download script](../utils/Download_model.py).

```bash
python ../utils/Download_model.py --model_name meta-llama/Llama-2-7b
```
The script prints the path where the model is downloaded as below.

`model/models--meta-llama--Llama-2-7b/snapshots/365ffa8f1a6c455d3e2028ae658236b4b85ba824`


### Step 3: Convert the "Meta" checkpoints to PyTorch Distributed compliant checkpoints

Convert the checkpoints to  PT-D compliant checkpoints as follows, note that for 7B `model_parallel_size 1` for 13B would be `model_parallel_size 2` and 70B `model_parallel_size 8`, you can also set `--nproc_per_node ` accordingly. PT-D compliant support flexible world_size when loading back the checkpoints into TP(lized) model. 

You would be able to use larger number of processes/ TP size when load the model back. For example if you have converted the `13B` checkpoints with `--nproc_per_node 2`, during the inference you can use `--nproc_per_node 8` which you are changing the world_size and effectively the TP size.


This will save the model args in `model_args.json`, during the inference step you need to pass this json file for build the model.

```
torchrun --nnodes 1 --nproc_per_node 8 convert_checkpoints.py --original_ckpt_dir  PATH/TO/MODEL/CHECKPOINTS  --tokenizer_path PATH/TO/MODEL/CHECKPOINTS/tokenizer.model --model_parallel_size 1 --save_checkpoint_dir converted_checkpoints

```



### Step 4: set up the configs:

Lets setup configs in `model-config.yaml` 

```
#frontend settings
minWorkers: 1
maxWorkers: 1
maxBatchDelay: 200
responseTimeout: 300
parallelType: "tp"
deviceType: "gpu"

torchrun:
    nproc-per-node: 8 # TP size

handler:
    converted_ckpt_dir: "PATH/TO/converted_checkpoints"
    tokenizer_path: "/PATH/TO/MODEL/CHECKPOINTS/tokenizer.model"
    model_args_path: "PATH/TO/model_args.json"
    max_seq_len: 512
    max_batch_size: 6
    max_new_tokens: 200
    temperature: 0.6
    top_p: 0.9
    manual_seed: 40
    mode: "chat" #choices are text_completion, chat
```


### Step 5: Serve the model:

```
torchserve --ncs --start --model-store model_store --models llama.tar.gz

```

### Step 6: Send inference request:

Text completion example :


```bash

curl -v "http://localhost:8080/predictions/llama" -T sample_text.txt

```


Chat example :


```bash

curl -v "http://localhost:8080/predictions/llama" -T dialogs.txt

```