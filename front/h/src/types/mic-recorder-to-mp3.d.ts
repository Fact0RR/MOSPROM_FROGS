declare module "mic-recorder-to-mp3" {
  type RecorderOptions = {
    bitRate?: number;
    // The library supports other options, but we only type what we use.
  };

  export default class MicRecorder {
    constructor(options?: RecorderOptions);
    start(): Promise<void>;
    stop(): {
      getMp3(): Promise<[ArrayBuffer, Blob]>;
    };
  }
}


