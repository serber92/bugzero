let handler = jest.createMockFromModule("handler-lib");
handler = jest.fn((fn) => fn());

module.exports = handler;
