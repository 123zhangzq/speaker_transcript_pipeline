# Speaker Transcript Pipeline

## README guide

Use this README in order, but do not do every installation section.

Sections 4, 5, and 6 are for different operating systems. Choose only the one that matches your computer:

1. Use Section 4 if you are on macOS.
2. Use Section 5 if you are on Linux or Ubuntu.
3. Use Section 6 if you are on Windows.

After installation, use Section 7 to create your Hugging Face token, then use Section 8 whenever you want to run the tool.

Contents:

1. What this tool does
2. What you need before starting
3. Folder preparation
4. Installation on macOS
5. Installation on Linux / Ubuntu
6. Installation on Windows
7. Create a Hugging Face Account and Token
8. How to run the tool
9. How to choose model size
10. How to choose min_speakers and max_speakers
11. Output files explained
12. Manual speaker role mapping
13. Troubleshooting

## 1. What this tool does

This tool takes a video or audio recording and creates transcript files with timestamps and speaker labels such as `SPEAKER_00` and `SPEAKER_01`.

It runs locally on your computer. It does not use paid APIs. It does not upload your recording to an external transcription service.

The tool does not identify real-world roles. It will not label anyone as doctor, patient, nurse, interviewer, or anything similar. It only creates anonymous speaker labels.

## 2. What you need before starting

You need:

1. A Windows, macOS, or Linux computer.
2. Python installed.
3. Internet access for the initial setup.
4. A recording file, such as `meeting.mp4`, `meeting.wav`, or `interview.m4a`.

Optional but recommended:

1. An NVIDIA GPU for faster processing.

Do not worry if you do not have a Hugging Face account or token yet. This README will guide you through creating everything step by step.

## 3. Folder preparation

Put this project folder somewhere easy to find.

Example on macOS or Windows:

```text
Desktop/
  transcript/
    speaker_transcript_pipeline/
```

Inside the project folder, create a folder named `data` if it does not already exist.

Your folder can look like this:

```text
speaker_transcript_pipeline/
  data/
    meeting.mp4
  outputs/
  transcribe_with_speakers.py
```

Put your recording file inside the `data` folder.

Supported input formats:

1. `mp4`
2. `mov`
3. `mkv`
4. `wav`
5. `mp3`
6. `m4a`

## 4. Installation on macOS

Follow these steps in order.

### Step 1: Open Terminal

1. Open Finder.
2. Open Applications.
3. Open Utilities.
4. Open Terminal.

### Step 2: Go to the project folder

If the project is on your Desktop inside a folder named `transcript`, run:

```bash
cd ~/Desktop/transcript/speaker_transcript_pipeline
```

If your project is somewhere else, change the command so it points to your project folder.

### Step 3: Install ffmpeg with Homebrew

Check whether Homebrew is installed:

```bash
brew --version
```

If that command works, install ffmpeg:

```bash
brew install ffmpeg
```

Check that ffmpeg works:

```bash
ffmpeg -version
```

If `brew` is not found, install Homebrew from:

```text
https://brew.sh
```

Then close Terminal, open it again, return to the project folder, and run:

```bash
brew install ffmpeg
```

### Step 4: Create a virtual environment

Run:

```bash
python3 -m venv .venv
```

This creates a private Python environment for this project.

### Step 5: Activate the virtual environment

Run:

```bash
source .venv/bin/activate
```

After activation, your Terminal prompt may show `(.venv)`.

### Step 6: Install Python packages

Run:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This may take several minutes. The first setup downloads large model-related packages.

### Step 7: Create and set your Hugging Face token

Follow Section 7 of this README. Do this in the same Terminal window if possible.

### Step 8: Check GPU before running

Run this command:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

If the second line says `True`, the script can use CUDA GPU mode.

If the second line says `False`, the script will use CPU mode. On most Macs, this is normal.

### Step 9: Run a test command

Make sure your recording is in the `data` folder. For example:

```text
data/meeting.mp4
```

Then run:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting \
  --model medium
```

When it finishes, open:

```text
outputs/meeting/
```

## 5. Installation on Linux / Ubuntu

Follow these steps in order.

### Step 1: Open Terminal

Open the Terminal application.

### Step 2: Go to the project folder

Example:

```bash
cd ~/Desktop/transcript/speaker_transcript_pipeline
```

If your project is somewhere else, change the path.

### Step 3: Install ffmpeg and Python tools

Run:

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv python3-pip
```

Check that ffmpeg works:

```bash
ffmpeg -version
```

### Step 4: Create a virtual environment

Run:

```bash
python3 -m venv .venv
```

### Step 5: Activate the virtual environment

Run:

```bash
source .venv/bin/activate
```

After activation, your Terminal prompt may show `(.venv)`.

### Step 6: Install Python packages

Run:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This may take several minutes.

### Step 7: Create and set your Hugging Face token

Follow Section 7 of this README. Do this in the same Terminal window if possible.

### Step 8: Check GPU before running

If you have an NVIDIA GPU, first check whether Linux can see it:

```bash
nvidia-smi
```

Then check whether PyTorch can use CUDA:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

If it prints `True` and shows your GPU name, the script can use GPU mode.

If `nvidia-smi` works but PyTorch prints `False`, see Section 13.

If you do not have an NVIDIA GPU, this is okay. The script will use CPU mode.

### Step 9: Run the script

Example:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting \
  --model medium
```

## 6. Installation on Windows

These steps assume you are using PowerShell.

### Step 1: Open PowerShell

1. Click the Start menu.
2. Type `PowerShell`.
3. Open Windows PowerShell.

### Step 2: Go to the project folder

If the project is on your Desktop inside a folder named `transcript`, run:

```powershell
cd "$HOME\Desktop\transcript\speaker_transcript_pipeline"
```

If your project is somewhere else, change the path.

### Step 3: Create a virtual environment

Run:

```powershell
py -3 -m venv .venv
```

If `py` is not found, try:

```powershell
python -m venv .venv
```

### Step 4: Activate the virtual environment

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell says scripts are disabled, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, your PowerShell prompt may show `(.venv)`.

### Step 5: Install requirements

Run:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This may take several minutes.

### Step 6: Install ffmpeg

Try this command first:

```powershell
winget install Gyan.FFmpeg
```

After installation, close PowerShell and open it again. Return to the project folder:

```powershell
cd "$HOME\Desktop\transcript\speaker_transcript_pipeline"
```

Activate the virtual environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

If `winget` is not available, download ffmpeg from:

```text
https://www.gyan.dev/ffmpeg/builds/
```

Choose a release build, unzip it, and add the `bin` folder to your Windows PATH.

### Step 7: Check ffmpeg works

Run:

```powershell
ffmpeg -version
```

If you see version information, ffmpeg is ready.

### Step 8: Create and set your Hugging Face token

Follow Section 7 of this README. Do this in the same PowerShell window if possible.

### Step 9: Check GPU before running

If you have an NVIDIA GPU, first check whether Windows can see it:

```powershell
nvidia-smi
```

Then check whether PyTorch can use CUDA:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

If it prints `True` and shows your GPU name, the script can use GPU mode.

If `nvidia-smi` works but PyTorch prints `False`, see Section 13.

If you do not have an NVIDIA GPU, this is okay. The script will use CPU mode.

### Step 10: Run the script

Example:

```powershell
python transcribe_with_speakers.py `
  --input data/meeting.mp4 `
  --output_dir outputs/meeting `
  --model medium
```

## 7. Create a Hugging Face Account and Token

This step only needs to be done once.

The token is free. It is not a payment method. It is only used to download the speaker diarization model to your local computer.

Your recording is not uploaded to Hugging Face by this script.

### Step 1: Create a Hugging Face account

1. Open a browser.
2. Go to:

```text
https://huggingface.co
```

3. Click Sign Up.
4. Create an account.
5. Verify your email address.

### Step 2: Create a Read Access Token

1. Log in to Hugging Face.
2. Click your profile picture.
3. Open Settings.
4. Open Access Tokens.
5. Click Create new token.
6. Choose Read permission.
7. Name the token something simple, such as:

```text
speaker-transcript
```

8. Click Create Token.
9. Copy the token.

The token should look like this:

```text
hf_xxxxxxxxxxxxxxxxxxxxxxxxx
```

Save it somewhere private. Do not post it online.

### Step 3: Accept pyannote model access

Open this page:

```text
https://huggingface.co/pyannote/speaker-diarization-3.1
```

Then:

1. Make sure you are logged in.
2. Click Access repository or Agree and access repository.
3. Accept the model terms.

Newer versions of this tool may also ask for access to another related pyannote model, such as:

```text
https://huggingface.co/pyannote/speaker-diarization-community-1
```

If Hugging Face asks you to accept another related pyannote model, accept that model's terms too.

### Step 4: Set the token on the computer

For macOS or Linux, run:

```bash
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"
```

For Windows PowerShell, run:

```powershell
$env:HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"
```

Replace `hf_xxxxxxxxxxxxxxxxx` with your real token.

### Step 5: Verify the token

For macOS or Linux:

```bash
echo $HF_TOKEN
```

For Windows PowerShell:

```powershell
echo $env:HF_TOKEN
```

If the token appears in the terminal, it is set for the current terminal window.

If you close the terminal, you may need to set it again.

Optional: you can also copy `.env.example` to `.env` and put your token there:

```text
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

Keep `.env` private.

## 8. How to run the tool

If you closed Terminal or PowerShell after installation, that is normal.

Each time you open a new Terminal or PowerShell window, do these setup steps before running the script.

### Step 1: Go to the project folder

macOS / Linux:

```bash
cd ~/Desktop/transcript/speaker_transcript_pipeline
```

Windows PowerShell:

```powershell
cd "$HOME\Desktop\transcript\speaker_transcript_pipeline"
```

If your project is somewhere else, change the path.

You should now be inside this folder:

```text
speaker_transcript_pipeline/
```

### Step 2: Activate the virtual environment

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, your command line should show `(.venv)`.

If you also see `(base)` on Windows, that is okay. The important part is that you see `(.venv)`.

### Step 3: Set your Hugging Face token again

If you closed the old Terminal or PowerShell window, set the token again.

macOS / Linux:

```bash
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"
```

Windows PowerShell:

```powershell
$env:HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"
```

Replace `hf_xxxxxxxxxxxxxxxxx` with your real token.

### Step 4: Check that the token is set

macOS / Linux:

```bash
echo $HF_TOKEN
```

Windows PowerShell:

```powershell
echo $env:HF_TOKEN
```

If your token appears, the token is set. Next, check GPU availability.

### Step 5: Check GPU before running

If you have an NVIDIA GPU on Windows or Linux, first check whether the computer can see it:

Linux with NVIDIA GPU:

```bash
nvidia-smi
```

Windows PowerShell:

```powershell
nvidia-smi
```

Then check whether PyTorch can use CUDA inside this virtual environment.

macOS / Linux:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

Windows PowerShell:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

If it prints `True` and shows your GPU name, the script can use GPU mode.

If `nvidia-smi` works but PyTorch prints `False`, see Section 13.

If you do not have an NVIDIA GPU, this is okay. The script will use CPU mode.

On most Macs, CUDA GPU mode is not available. CPU mode is expected.

### Step 6: Run one of the commands below

Choose the example that matches your recording.

### Example 1: Basic command

macOS / Linux:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting
```

Windows PowerShell:

```powershell
python transcribe_with_speakers.py `
  --input data/meeting.mp4 `
  --output_dir outputs/meeting
```

### Example 2: If you know there are 2 to 4 speakers

macOS / Linux:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting \
  --min_speakers 2 \
  --max_speakers 4
```

Windows PowerShell:

```powershell
python transcribe_with_speakers.py `
  --input data/meeting.mp4 `
  --output_dir outputs/meeting `
  --min_speakers 2 `
  --max_speakers 4
```

### Example 3: Use a smaller model for weaker computers

macOS / Linux:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting \
  --model medium \
  --compute_type int8
```

Windows PowerShell:

```powershell
python transcribe_with_speakers.py `
  --input data/meeting.mp4 `
  --output_dir outputs/meeting `
  --model medium `
  --compute_type int8
```

### Example 4: Chinese recording

macOS / Linux:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting \
  --language zh \
  --min_speakers 2 \
  --max_speakers 4
```

Windows PowerShell:

```powershell
python transcribe_with_speakers.py `
  --input data/meeting.mp4 `
  --output_dir outputs/meeting `
  --language zh `
  --min_speakers 2 `
  --max_speakers 4
```

## 9. How to choose model size

Use this simple guide:

1. `large-v3`: best accuracy, but needs a stronger computer. Best with a good NVIDIA GPU.
2. `medium`: good balance. Start here if you are unsure.
3. `small`: faster, but less accurate.

Recommended starting point:

```bash
--model medium
```

Use `large-v3` if your computer has a good NVIDIA GPU and you want the best accuracy.

## 10. How to choose min_speakers and max_speakers

These settings tell the tool how many different voices to expect.

If you know there are probably 2 speakers:

```bash
--min_speakers 2 --max_speakers 2
```

If you are not sure, but you think there are 2 to 5 speakers:

```bash
--min_speakers 2 --max_speakers 5
```

If you do not know at all, leave them empty.

## 11. Output files explained

The script creates these files inside your output folder.

### transcript_segments.json

Machine-readable output for research.

Use this file for downstream analysis.

Each item has:

1. `speaker`
2. `start`
3. `end`
4. `text`

Example:

```json
[
  {
    "speaker": "SPEAKER_00",
    "start": 12.34,
    "end": 16.8,
    "text": "Can you tell me today's date?"
  }
]
```

### transcript_readable.txt

Human-readable transcript.

Use this file for manual checking.

Example:

```text
[00:00:12.340 - 00:00:16.800] SPEAKER_00:
Can you tell me today's date?
```

### transcript.srt

Subtitle file.

You can use this with video players or subtitle tools.

Example:

```srt
1
00:00:12,340 --> 00:00:16,800
SPEAKER_00: Can you tell me today's date?
```

### speaker_role_mapping_template.json

Manual speaker mapping template.

The tool leaves the role values empty.

Use this file later if you want to manually map anonymous labels to real roles.

Example:

```json
{
  "recording_id": "meeting",
  "speaker_role_mapping": {
    "SPEAKER_00": "",
    "SPEAKER_01": ""
  }
}
```

Recommended use:

1. Use `transcript_segments.json` for downstream analysis.
2. Use `transcript_readable.txt` for manual checking.
3. Use `speaker_role_mapping_template.json` to manually map `SPEAKER_00` to doctor, patient, or another role later.

## 12. Manual speaker role mapping

The tool does not know who is doctor or patient.

It only knows that different voices are present.

After transcription:

1. Open `transcript_readable.txt`.
2. Inspect the first few lines.
3. Decide who each anonymous speaker label refers to.
4. Open `speaker_role_mapping_template.json`.
5. Fill in the values manually.

Example after you manually fill it in:

```json
{
  "recording_id": "meeting",
  "speaker_role_mapping": {
    "SPEAKER_00": "doctor",
    "SPEAKER_01": "patient"
  }
}
```

This manual mapping is done after transcription. The transcription script itself does not fill in real roles.

## 13. Troubleshooting

### Problem: ffmpeg not found

Check ffmpeg:

```bash
ffmpeg -version
```

If the command does not work, install ffmpeg.

macOS:

```bash
brew install ffmpeg
```

Ubuntu:

```bash
sudo apt update
sudo apt install -y ffmpeg
```

Windows PowerShell:

```powershell
winget install Gyan.FFmpeg
```

After installing on Windows, close PowerShell and open it again.

### Problem: HF_TOKEN missing

Set the token again.

macOS / Linux:

```bash
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"
```

Windows PowerShell:

```powershell
$env:HF_TOKEN="hf_xxxxxxxxxxxxxxxxx"
```

Then verify it.

macOS / Linux:

```bash
echo $HF_TOKEN
```

Windows PowerShell:

```powershell
echo $env:HF_TOKEN
```

### Problem: pyannote access denied

This usually means the token exists, but your Hugging Face account has not accepted the model terms.

Open:

```text
https://huggingface.co/pyannote/speaker-diarization-3.1
```

Make sure you are logged in. Click Access repository or Agree and access repository.

If Hugging Face asks you to accept another related pyannote model, accept that too.

Also check that your token has Read permission.

### Problem: CUDA out of memory

Try a smaller model and lighter compute type:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting \
  --model medium \
  --compute_type int8
```

You can also try:

```bash
--model small
--compute_type int8
```

### Problem: I have an NVIDIA GPU, but the script says CUDA GPU not detected

This usually means the virtual environment installed the CPU-only version of PyTorch.

First, check whether Windows can see your NVIDIA GPU:

```powershell
nvidia-smi
```

If this command works, your NVIDIA driver is visible.

Look near the top of the output for `CUDA Version`.

For this project, the current dependency set uses PyTorch 2.8.0. On Windows, PyTorch 2.8.0 provides CUDA packages for CUDA 12.6, 12.8, and 12.9.

If `nvidia-smi` shows an older CUDA version, such as `CUDA Version: 12.2`, update your NVIDIA driver first.

The easiest way on Windows is:

1. Open NVIDIA App or GeForce Experience.
2. Install the latest NVIDIA driver.
3. Restart the computer.
4. Open PowerShell again.
5. Run `nvidia-smi` again.

After updating, it is best if `nvidia-smi` shows `CUDA Version: 12.8` or newer.

Next, check what PyTorch can see:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

If the version shows `+cpu` or the second line says `False`, reinstall the CUDA version of PyTorch.

Run these commands inside the activated `(.venv)` environment:

```powershell
python -m pip uninstall -y torch torchvision torchaudio
python -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
```

If your updated driver only shows `CUDA Version: 12.6` or `CUDA Version: 12.7`, use this command instead:

```powershell
python -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
```

Then check again:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

If it prints `True` and shows your GPU name, run the transcription command again.

If `nvidia-smi` does not work, install or update the NVIDIA driver first.

This tool needs an NVIDIA CUDA GPU for GPU mode. Intel and AMD GPUs usually do not work with this setup on Windows.

### Problem: The transcript is inaccurate

Try:

1. Use `--model large-v3`.
2. Improve the audio quality if possible.
3. Specify the language.

Example:

```bash
--language en
```

For Chinese:

```bash
--language zh
```

### Problem: Speaker labels are wrong

Try:

1. Set `--min_speakers` and `--max_speakers`.
2. Try a cleaner audio file.
3. Reduce background noise if possible.

Example:

```bash
--min_speakers 2 --max_speakers 2
```

### Problem: The program is very slow

This is normal on CPU.

Try:

1. Use an NVIDIA GPU if available.
2. Use `--model medium`.
3. Use `--model small`.
4. Use `--compute_type int8`.

Example:

```bash
python transcribe_with_speakers.py \
  --input data/meeting.mp4 \
  --output_dir outputs/meeting \
  --model medium \
  --compute_type int8
```
