const axios = require('axios');
const SLACK_HOOK_API_ERRORS = process.env.SLACK_HOOK_API_ERRORS;

async function log(mrkdwn) {
  try {
    await axios.post(SLACK_HOOK_API_ERRORS, {
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: mrkdwn,
          },
        },
      ],
    });
  } catch (e) {
    console.log('Failed to log to slack.');
  }
}

async function error(e) {
  try {
    await axios.post(
      SLACK_HOOK_API_ERRORS,

      {
        blocks: [
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: `🚨 [ERROR] ${e.message}`,
            },
          },
          {
            type: 'divider',
          },
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: ` \`\`\` ${e.stack} \`\`\` `,
            },
          },
        ],
      }
    );
  } catch (e) {
    console.log('Failed to log to slack.');
  }
}

module.exports = {
  log,
  error,
};
