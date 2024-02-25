import yaml
from transformers import AutoConfig, AutoModelForCausalLM

from stripedhyena.utils import dotdict
from stripedhyena.model import StripedHyena
from stripedhyena.tokenizer import CharLevelTokenizer


MODEL_NAMES = ['evo-1-phase-1', 'evo-1-phase-2']

class Evo:
    def __init__(self, model_name: str = MODEL_NAMES[0], device: str = None):
        """
        Loads an Evo model checkpoint given a model name.
        If the checkpoint does not exist, we automatically download it from HuggingFace.
        """
        self.device = device

        # Check model name.

        if model_name not in MODEL_NAMES:
            raise ValueError(
                f'Invalid model name {model_name}. Should be one of: '
                f'{", ".join(MODEL_NAMES)}.'
            )

        # Assign config path.

        if model_name == 'evo-1-phase-1':
            config_path = 'evo/configs/evo-1-phase-1_inference.yml'
        elif model_name == 'evo-1-phase-2':
            config_path = 'evo/configs/evo-1-phase-2_inference.yml'
        else:
            raise ValueError(
                f'Invalid model name {model_name}. Should be one of: '
                f'{", ".join(MODEL_NAMES)}.'
            )

        # Load model.

        self.model = load_checkpoint(
            model_name=model_name,
            config_path=config_path,
            device=self.device
        )

        # Load tokenizer.

        self.tokenizer = CharLevelTokenizer(512)

        
# TODO: update links to checkpoints from Together
HF_MODEL_NAME_MAP = {
    'evo-1-phase-1': 'LongSafari/Evo-1', # togethercomputer/Evo-1-phase-1
    'evo-1-phase-2': 'LongSafari/Evo-1-IS110-SFT', # togethercomputer/Evo-1-phase-2
}

def load_checkpoint(
    model_name: str = MODEL_NAMES[0],
    config_path: str = 'evo/configs/evo-1-phase-1_inference.yml',
    device: str = None,
    *args, **kwargs
):
    """
    Load checkpoint from HuggingFace and place it into SH model.
    """

    # Map model name to HuggingFace model name.

    hf_model_name = HF_MODEL_NAME_MAP[model_name]

    # Load model config.

    model_config = AutoConfig.from_pretrained(hf_model_name, trust_remote_code=True)
    model_config.use_cache = True

    # Load model.

    model = AutoModelForCausalLM.from_pretrained(
        hf_model_name,
        config=model_config,
        trust_remote_code=True,
    )

    # Load model state dict & cleanup.

    state_dict = model.backbone.state_dict()
    del model
    del model_config

    # Load SH config.

    global_config = dotdict(yaml.load(open(config_path), Loader=yaml.FullLoader))

    # Load SH Model.

    model = StripedHyena(global_config)
    model.load_state_dict(state_dict, strict=True)
    model.to_bfloat16_except_poles_residues()
    if device is not None:
        model = model.to(device)

    return model