export const QuestionCard = () => {
  return (
    <div className="question-card" data-asset-id="ASSET_02_01">
      <div className="question-text">帮我看看这份保险条款有哪些坑？</div>
      <div className="question-meta">用户输入</div>
    </div>
  );
};

export const PlainAnswerCard = ({scroll}: {scroll: number}) => {
  return (
    <div className="plain-answer-card" data-asset-id="ASSET_02_02">
      <div
        className="plain-answer-inner"
        style={{
          transform: `translateY(${-scroll}px)`,
        }}
      >
        <div className="plain-answer-title">普通回答</div>
        {[
          '本产品保障多种重大疾病，等待期为90天，赔付比例依据合同条款约定执行。',
          '保险期间内，如被保险人首次确诊合同约定疾病，保险公司将按照基本保险金额给付保险金。',
          '投保前请仔细阅读保险责任、责任免除、犹豫期、现金价值及相关服务说明。',
          '以上内容仅供参考，具体以保险合同和保险公司解释为准。',
        ].map((line) => (
          <div className="plain-answer-line" key={line}>
            {line}
          </div>
        ))}
      </div>
    </div>
  );
};

export const ExpertAnswerCard = ({
  greenClip,
  orangeClip,
}: {
  greenClip: number;
  orangeClip: number;
}) => {
  return (
    <div className="expert-card" data-asset-id="ASSET_03_01">
      <div className="expert-card-title">专家回答：这份保险先看三个风险点</div>
      <div className="expert-card-subtitle">不是复述条款，而是直接指出容易漏看的地方。</div>
      <ExpertRow
        label="免责条款"
        text="是否把既往症、职业风险、等待期内确诊排除在外。"
        highlight="green"
        clip={greenClip}
      />
      <ExpertRow
        label="赔付条件"
        text="看着都是“确诊即赔”，实际可能要求病理、手术或严重程度。"
        highlight="orange"
        clip={orangeClip}
      />
      <ExpertRow label="附录小字" text="部分保障范围、医院限制、报销比例会藏在附录几行字里。" />
    </div>
  );
};

const ExpertRow = ({
  label,
  text,
  highlight,
  clip = 0,
}: {
  label: string;
  text: string;
  highlight?: 'green' | 'orange';
  clip?: number;
}) => {
  return (
    <div className="expert-row">
      <span className="expert-row-label">{label}</span>
      <span className="expert-row-text">
        {highlight ? (
          <span
            className={`highlight-bar highlight-${highlight}`}
            style={{
              clipPath: `inset(0 ${100 - clip * 100}% 0 0)`,
            }}
          />
        ) : null}
        {text}
      </span>
    </div>
  );
};

export const Magnifier = () => {
  return (
    <div className="magnifier" data-asset-id="ASSET_03_02">
      <div className="magnifier-title">附录小字</div>
      <div className="magnifier-body">
        免赔责任：既往症、等待期内症状、非指定医院记录可能影响赔付。
      </div>
      <div className="magnifier-handle" />
    </div>
  );
};

export const PromptCard = ({variant}: {variant: 'guide' | 'super'}) => {
  const isGuide = variant === 'guide';
  const lines = isGuide
    ? ['角色：保险顾问', '任务：找出隐藏风险', '输出：按严重程度排序', '限制：不要只复述条款']
    : ['请先识别免责条款', '再比较赔付触发条件', '最后检查附录与小字', '把不确定处单独标出'];

  return (
    <div className="prompt-card" data-asset-id={isGuide ? 'ASSET_04_01' : 'ASSET_04_02'}>
      <div className="prompt-card-title">{isGuide ? '提问指南' : '超级 Prompt'}</div>
      <div className={`prompt-rule ${isGuide ? 'prompt-blue' : 'prompt-red'}`} />
      {lines.map((line) => (
        <div className="prompt-line" key={line}>
          {line}
        </div>
      ))}
    </div>
  );
};

export const QuestionMark = () => {
  return (
    <div className="question-mark" data-asset-id="ASSET_04_03">
      ?
    </div>
  );
};

