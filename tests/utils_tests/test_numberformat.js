const { format } = require('../../django/utils/numberformat');

describe('numberformat', () => {
    test('handles empty string without IndexError', () => {
        expect(() => {
            format('', '.', 2, 0, ',');
        }).not.toThrow();
    });

    test('handles null value without IndexError', () => {
        expect(() => {
            format(null, '.', 2, 0, ',');
        }).not.toThrow();
    });

    test('handles undefined value without IndexError', () => {
        expect(() => {
            format(undefined, '.', 2, 0, ',');
        }).not.toThrow();
    });

    test('formats normal negative number correctly', () => {
        const result = format(-123.45, '.', 2, 0, ',');
        expect(result).toBe('-123.45');
    });

    test('formats normal positive number correctly', () => {
        const result = format(123.45, '.', 2, 0, ',');
        expect(result).toBe('123.45');
    });

    test('formats zero correctly', () => {
        const result = format(0, '.', 2, 0, ',');
        expect(result).toBe('0.00');
    });
});
