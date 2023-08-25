module.exports = {
  env: {
    node: true,
    commonjs: true,
    es6: true,
  },
  extends: ["eslint:recommended", "plugin:prettier/recommended"],
  globals: {
    Atomics: "readonly",
    SharedArrayBuffer: "readonly",
    document: false,
  },
  parserOptions: {
    ecmaVersion: 2018,
  },
  plugins: ["prettier"],
  rules: { "prettier/prettier": "error" },
};
