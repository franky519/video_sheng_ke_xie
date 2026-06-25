import { Composition } from "remotion";
import { RankingAnimation } from "./RankingAnimation";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="RankingAnimation"
      component={RankingAnimation}
      durationInFrames={30 * 8}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
