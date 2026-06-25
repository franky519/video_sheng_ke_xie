import { Composition } from "remotion";
import { Sequence01Typing } from "./Sequence01_Typing";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Sequence01"
        component={Sequence01Typing}
        durationInFrames={30 * 8}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
