const { ValidationError } = require('../../django/core/exceptions');

describe('ValidationError Equality Tests', () => {
    test('ValidationErrors with identical string messages should be equal', () => {
        const error1 = new ValidationError("This field is required.");
        const error2 = new ValidationError("This field is required.");
        expect(error1).toEqual(error2);
    });

    test('ValidationErrors with same messages in different order should be equal', () => {
        const error3 = new ValidationError(["Error A", "Error B"]);
        const error4 = new ValidationError(["Error B", "Error A"]);
        expect(error3).toEqual(error4);
    });

    test('ValidationErrors with same field errors in different order should be equal', () => {
        const error5 = new ValidationError({"field1": ["Error 1"], "field2": ["Error 2"]});
        const error6 = new ValidationError({"field2": ["Error 2"], "field1": ["Error 1"]});
        expect(error5).toEqual(error6);
    });

    test('ValidationErrors with different messages should not be equal', () => {
        const error7 = new ValidationError("Different message");
        const error8 = new ValidationError("Another message");
        expect(error7).not.toEqual(error8);
    });

    test('ValidationError should not equal non-ValidationError objects', () => {
        const error = new ValidationError("Test message");
        expect(error).not.toEqual("Test message");
        expect(error).not.toEqual({});
        expect(error).not.toEqual(null);
    });

    test('ValidationErrors with different field sets should not be equal', () => {
        const error1 = new ValidationError({"field1": ["Error 1"]});
        const error2 = new ValidationError({"field2": ["Error 1"]});
        expect(error1).not.toEqual(error2);
    });

    test('ValidationError with error_dict should not equal one with error_list', () => {
        const error1 = new ValidationError({"field1": ["Error 1"]});
        const error2 = new ValidationError(["Error 1"]);
        expect(error1).not.toEqual(error2);
    });

    test('Empty ValidationErrors should be equal', () => {
        const error1 = new ValidationError([]);
        const error2 = new ValidationError([]);
        expect(error1).toEqual(error2);
    });

    test('ValidationErrors with nested ValidationError objects should be equal', () => {
        const nestedError1 = new ValidationError("Nested error");
        const nestedError2 = new ValidationError("Nested error");
        const error1 = new ValidationError([nestedError1]);
        const error2 = new ValidationError([nestedError2]);
        expect(error1).toEqual(error2);
    });
});
