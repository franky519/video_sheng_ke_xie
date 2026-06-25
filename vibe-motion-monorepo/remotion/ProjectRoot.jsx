import { Composition } from "remotion";
import { DoubaoScience30 } from "../shared/project-main/src/composition/DoubaoScience30";
import { Sequence01Typing } from "../shared/project-screen-record/src/Sequence01_Typing";
import { RankingAnimation as RankingAnimation0 } from "../shared/project-code-data-0/src/RankingAnimation";
import { RankingAnimation as RankingAnimation1 } from "../shared/project-code-data-1/src/RankingAnimation";

export const ProjectRoot = () => {
  return (
    <>
      <Composition
        id="DoubaoScience30"
        component={DoubaoScience30}
        durationInFrames={864}
        fps={24}
        width={1280}
        height={720}
        defaultProps={{ showDebugLabels: false }}
      />
      <Composition
        id="DoubaoScience30-Debug"
        component={DoubaoScience30}
        durationInFrames={864}
        fps={24}
        width={1280}
        height={720}
        defaultProps={{ showDebugLabels: true }}
      />
      <Composition
        id="Sequence01"
        component={Sequence01Typing}
        durationInFrames={30 * 8}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="RankingAnimation"
        component={RankingAnimation0}
        durationInFrames={30 * 8}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="RankingAnimation-AI"
        component={RankingAnimation1}
        durationInFrames={30 * 8}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
