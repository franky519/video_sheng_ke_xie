import {Composition} from 'remotion';
import {DoubaoScience30} from './composition/DoubaoScience30';

export const Root = () => {
  return (
    <>
      <Composition
        id="DoubaoScience30"
        component={DoubaoScience30}
        durationInFrames={720}
        fps={24}
        width={1280}
        height={720}
        defaultProps={{showDebugLabels: false}}
      />
      <Composition
        id="DoubaoScience30-Debug"
        component={DoubaoScience30}
        durationInFrames={720}
        fps={24}
        width={1280}
        height={720}
        defaultProps={{showDebugLabels: true}}
      />
    </>
  );
};
