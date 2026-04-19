const { describe, it, expect, beforeEach, afterEach } = require('@jest/globals');
const { Model, CharField, OneToOneField, CASCADE } = require('../src/models');
const { QuerySet } = require('../src/queryset');
const { Database } = require('../src/database');

// Mock models for testing
class Main extends Model {
    static fields = {
        id: { type: 'AutoField', primaryKey: true },
        main_field_1: { type: 'CharField', maxLength: 45, blank: true },
        main_field_2: { type: 'CharField', maxLength: 45, blank: true },
        main_field_3: { type: 'CharField', maxLength: 45, blank: true }
    };
    
    static tableName = 'main';
}

class Secondary extends Model {
    static fields = {
        main: { 
            type: 'OneToOneField', 
            to: Main, 
            primaryKey: true, 
            relatedName: 'secondary', 
            onDelete: CASCADE 
        },
        secondary_field_1: { type: 'CharField', maxLength: 45, blank: true },
        secondary_field_2: { type: 'CharField', maxLength: 45, blank: true },
        secondary_field_3: { type: 'CharField', maxLength: 45, blank: true }
    };
    
    static tableName = 'secondary';
}

describe('QuerySet.only() with select_related() on reverse OneToOneField', () => {
    let db;
    let mainQuerySet;
    
    beforeEach(() => {
        db = new Database(':memory:');
        mainQuerySet = new QuerySet(Main, db);
        
        // Setup test data
        db.execute(`
            CREATE TABLE main (
                id INTEGER PRIMARY KEY,
                main_field_1 VARCHAR(45),
                main_field_2 VARCHAR(45),
                main_field_3 VARCHAR(45)
            )
        `);
        
        db.execute(`
            CREATE TABLE secondary (
                main_id INTEGER PRIMARY KEY,
                secondary_field_1 VARCHAR(45),
                secondary_field_2 VARCHAR(45),
                secondary_field_3 VARCHAR(45),
                FOREIGN KEY (main_id) REFERENCES main(id)
            )
        `);
        
        // Insert test data
        db.execute(`
            INSERT INTO main (id, main_field_1, main_field_2, main_field_3) 
            VALUES (1, 'main1', 'main2', 'main3')
        `);
        
        db.execute(`
            INSERT INTO secondary (main_id, secondary_field_1, secondary_field_2, secondary_field_3) 
            VALUES (1, 'sec1', 'sec2', 'sec3')
        `);
    });
    
    afterEach(() => {
        if (db) {
            db.close();
        }
    });
    
    it('should only select specified fields when using only() with select_related() on reverse OneToOne', () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only('main_field_1', 'secondary__secondary_field_1');
        
        const sql = queryset.toSQL();
        
        // The generated SQL should only include the specified fields
        expect(sql.query).toContain('main.main_field_1');
        expect(sql.query).toContain('secondary.secondary_field_1');
        
        // Should NOT contain the non-specified fields
        expect(sql.query).not.toContain('main.main_field_2');
        expect(sql.query).not.toContain('main.main_field_3');
        expect(sql.query).not.toContain('secondary.secondary_field_2');
        expect(sql.query).not.toContain('secondary.secondary_field_3');
        
        // Verify the JOIN is still present
        expect(sql.query).toContain('LEFT OUTER JOIN secondary');
    });
    
    it('should handle only() with just main model fields and select_related()', () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only('main_field_1');
        
        const sql = queryset.toSQL();
        
        expect(sql.query).toContain('main.main_field_1');
        expect(sql.query).not.toContain('main.main_field_2');
        expect(sql.query).not.toContain('main.main_field_3');
        
        // Should not include any secondary fields since none were specified in only()
        expect(sql.query).not.toContain('secondary.secondary_field_1');
        expect(sql.query).not.toContain('secondary.secondary_field_2');
        expect(sql.query).not.toContain('secondary.secondary_field_3');
    });
    
    it('should handle only() with just related model fields and select_related()', () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only('secondary__secondary_field_1');
        
        const sql = queryset.toSQL();
        
        expect(sql.query).toContain('secondary.secondary_field_1');
        expect(sql.query).not.toContain('secondary.secondary_field_2');
        expect(sql.query).not.toContain('secondary.secondary_field_3');
        
        // Should include the primary key of main model (required for the relation)
        expect(sql.query).toContain('main.id');
        
        // Should not include other main fields
        expect(sql.query).not.toContain('main.main_field_1');
        expect(sql.query).not.toContain('main.main_field_2');
        expect(sql.query).not.toContain('main.main_field_3');
    });
    
    it('should work correctly when only() is called before select_related()', () => {
        const queryset = mainQuerySet
            .only('main_field_1', 'secondary__secondary_field_1')
            .select_related('secondary');
        
        const sql = queryset.toSQL();
        
        expect(sql.query).toContain('main.main_field_1');
        expect(sql.query).toContain('secondary.secondary_field_1');
        expect(sql.query).not.toContain('main.main_field_2');
        expect(sql.query).not.toContain('secondary.secondary_field_2');
    });
    
    it('should execute query and return correct data with limited fields', async () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only('main_field_1', 'secondary__secondary_field_1');
        
        const results = await queryset.all();
        
        expect(results).toHaveLength(1);
        const result = results[0];
        
        // Should have the specified fields
        expect(result.main_field_1).toBe('main1');
        expect(result.secondary.secondary_field_1).toBe('sec1');
        
        // Should not have the non-specified fields (or they should be undefined)
        expect(result.main_field_2).toBeUndefined();
        expect(result.main_field_3).toBeUndefined();
        expect(result.secondary.secondary_field_2).toBeUndefined();
        expect(result.secondary.secondary_field_3).toBeUndefined();
    });
    
    it('should handle multiple related field specifications correctly', () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only('main_field_1', 'main_field_2', 'secondary__secondary_field_1', 'secondary__secondary_field_3');
        
        const sql = queryset.toSQL();
        
        // Should include specified main fields
        expect(sql.query).toContain('main.main_field_1');
        expect(sql.query).toContain('main.main_field_2');
        expect(sql.query).not.toContain('main.main_field_3');
        
        // Should include specified secondary fields
        expect(sql.query).toContain('secondary.secondary_field_1');
        expect(sql.query).toContain('secondary.secondary_field_3');
        expect(sql.query).not.toContain('secondary.secondary_field_2');
    });
    
    it('should maintain correct behavior when no related fields are specified in only()', () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only('main_field_1');
        
        const sql = queryset.toSQL();
        
        // Should still perform the join for select_related
        expect(sql.query).toContain('LEFT OUTER JOIN secondary');
        
        // But should not select any secondary fields
        expect(sql.query).not.toContain('secondary.secondary_field_1');
        expect(sql.query).not.toContain('secondary.secondary_field_2');
        expect(sql.query).not.toContain('secondary.secondary_field_3');
    });
    
    it('should handle edge case with empty only() call', () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only();
        
        const sql = queryset.toSQL();
        
        // With empty only(), should only include primary keys
        expect(sql.query).toContain('main.id');
        expect(sql.query).not.toContain('main.main_field_1');
        expect(sql.query).not.toContain('secondary.secondary_field_1');
    });
});

describe('Regression test for Django 4.2 QuerySet.only() with select_related()', () => {
    let db;
    let mainQuerySet;
    
    beforeEach(() => {
        db = new Database(':memory:');
        mainQuerySet = new QuerySet(Main, db);
    });
    
    afterEach(() => {
        if (db) {
            db.close();
        }
    });
    
    it('should generate the same SQL as Django 4.1 for reverse OneToOne with only()', () => {
        const queryset = mainQuerySet
            .select_related('secondary')
            .only('main_field_1', 'secondary__secondary_field_1');
        
        const sql = queryset.toSQL();
        
        // Expected SQL pattern (similar to Django 4.1 behavior)
        const expectedPattern = /SELECT\s+main\.id,\s*main\.main_field_1,\s*secondary\.main_id,\s*secondary\.secondary_field_1\s+FROM\s+main\s+LEFT\s+OUTER\s+JOIN\s+secondary/i;
        
        expect(sql.query).toMatch(expectedPattern);
        
        // Ensure it doesn't include all fields (Django 4.2 regression)
        expect(sql.query).not.toContain('main_field_2');
        expect(sql.query).not.toContain('main_field_3');
        expect(sql.query).not.toContain('secondary_field_2');
        expect(sql.query).not.toContain('secondary_field_3');
    });
});