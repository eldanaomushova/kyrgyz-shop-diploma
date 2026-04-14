module.exports = {
    extends: ["react-app", "react-app/jest"],
    rules: {
        "no-unused-vars": "error",
        "react-hooks/exhaustive-deps": "warn",
        "jsx-a11y/anchor-is-valid": "error",
        "no-console": "warn",
        "no-debugger": "error",
        "no-duplicate-imports": "error",
        "no-unreachable": "error",
        "react/prop-types": "off",
    },
};
