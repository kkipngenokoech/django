const { describe, it, expect, beforeEach, afterEach } = require('@jest/globals');
const { Model, Field, Meta } = require('../../src/models');
const { QuerySet } = require('../../src/query');
const { DatabaseConnection } = require('../../src/db');

describe('Model Inheritance Ordering', () => {
    let db;
    let Parent;
    let Child;

    beforeEach(async () => {
        db = new DatabaseConnection(':memory:');
        await db.connect();

        // Define Parent model with -pk ordering
        Parent = class extends Model {
            static get meta() {
                return new Meta({
                    ordering: ['-pk'],
                    tableName: 'test_parent'
                });
            }
        };

        // Define Child model inheriting from Parent
        Child = class extends Parent {
            static get meta() {
                return new Meta({
                    tableName: 'test_child'
                });
            }
        };

        // Create tables
        await db.execute(`
            CREATE TABLE test_parent (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        `);

        await db.execute(`
            CREATE TABLE test_child (
                parent_ptr_id INTEGER PRIMARY KEY,
                FOREIGN KEY (parent_ptr_id) REFERENCES test_parent(id)
            )
        `);

        // Insert test data
        await db.execute('INSERT INTO test_parent (id) VALUES (1), (2), (3)');
        await db.execute('INSERT INTO test_child (parent_ptr_id) VALUES (1), (2), (3)');
    });

    afterEach(async () => {
        await db.close();
    });

    it('should order Parent model by -pk correctly', async () => {
        const queryset = new QuerySet(Parent, db);
        const query = queryset.all().getQuery();
        
        expect(query.sql).toContain('ORDER BY "test_parent"."id" DESC');
        
        const results = await queryset.all().execute();
        expect(results.map(r => r.id)).toEqual([3, 2, 1]);
    });

    it('should inherit -pk ordering correctly in Child model', async () => {
        const queryset = new QuerySet(Child, db);
        const query = queryset.all().getQuery();
        
        // The key assertion - should be DESC not ASC
        expect(query.sql).toContain('ORDER BY "test_parent"."id" DESC');
        expect(query.sql).not.toContain('ORDER BY "test_parent"."id" ASC');
        
        const results = await queryset.all().execute();
        expect(results.map(r => r.parent_ptr_id)).toEqual([3, 2, 1]);
    });

    it('should handle multiple ordering fields in inheritance', async () => {
        // Define a more complex Parent with multiple ordering
        const ComplexParent = class extends Model {
            static get meta() {
                return new Meta({
                    ordering: ['-pk', 'name'],
                    tableName: 'test_complex_parent'
                });
            }
        };

        const ComplexChild = class extends ComplexParent {
            static get meta() {
                return new Meta({
                    tableName: 'test_complex_child'
                });
            }
        };

        await db.execute(`
            CREATE TABLE test_complex_parent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        `);

        await db.execute(`
            CREATE TABLE test_complex_child (
                parent_ptr_id INTEGER PRIMARY KEY,
                FOREIGN KEY (parent_ptr_id) REFERENCES test_complex_parent(id)
            )
        `);

        const queryset = new QuerySet(ComplexChild, db);
        const query = queryset.all().getQuery();
        
        expect(query.sql).toContain('ORDER BY "test_complex_parent"."id" DESC');
        expect(query.sql).toContain('"test_complex_parent"."name" ASC');
    });

    it('should preserve field ordering direction for non-pk fields', async () => {
        const ParentWithField = class extends Model {
            static get meta() {
                return new Meta({
                    ordering: ['-name', 'pk'],
                    tableName: 'test_parent_field'
                });
            }
        };

        const ChildWithField = class extends ParentWithField {
            static get meta() {
                return new Meta({
                    tableName: 'test_child_field'
                });
            }
        };

        await db.execute(`
            CREATE TABLE test_parent_field (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        `);

        await db.execute(`
            CREATE TABLE test_child_field (
                parent_ptr_id INTEGER PRIMARY KEY,
                FOREIGN KEY (parent_ptr_id) REFERENCES test_parent_field(id)
            )
        `);

        const queryset = new QuerySet(ChildWithField, db);
        const query = queryset.all().getQuery();
        
        expect(query.sql).toContain('ORDER BY "test_parent_field"."name" DESC');
        expect(query.sql).toContain('"test_parent_field"."id" ASC');
    });

    it('should handle pk field reference correctly', async () => {
        // Test that 'pk' is correctly resolved to the actual primary key field
        const queryset = new QuerySet(Child, db);
        const query = queryset.all().getQuery();
        
        // Should resolve 'pk' to 'id' and maintain DESC ordering
        expect(query.sql).toMatch(/ORDER BY.*"test_parent"\."id".*DESC/);
    });
});
