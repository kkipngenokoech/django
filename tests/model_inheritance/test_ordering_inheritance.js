const { describe, it, expect, beforeEach, afterEach } = require('@jest/globals');
const { Model, DataTypes, Sequelize } = require('sequelize');

describe('Model Inheritance Ordering Tests', () => {
  let sequelize;
  let Parent;
  let Child;

  beforeEach(async () => {
    // Setup in-memory SQLite database for testing
    sequelize = new Sequelize('sqlite::memory:', {
      logging: false
    });

    // Define Parent model with descending pk ordering
    Parent = sequelize.define('Parent', {
      id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
      }
    }, {
      tableName: 'parents',
      defaultScope: {
        order: [['id', 'DESC']]
      }
    });

    // Define Child model that inherits from Parent
    Child = sequelize.define('Child', {
      parentId: {
        type: DataTypes.INTEGER,
        references: {
          model: Parent,
          key: 'id'
        }
      }
    }, {
      tableName: 'children'
    });

    // Set up inheritance relationship
    Child.belongsTo(Parent, { foreignKey: 'parentId' });
    Parent.hasMany(Child, { foreignKey: 'parentId' });

    await sequelize.sync({ force: true });
  });

  afterEach(async () => {
    await sequelize.close();
  });

  it('should correctly inherit descending pk ordering from parent model', async () => {
    // Create some test data
    const parent1 = await Parent.create({});
    const parent2 = await Parent.create({});
    const parent3 = await Parent.create({});

    const child1 = await Child.create({ parentId: parent1.id });
    const child2 = await Child.create({ parentId: parent2.id });
    const child3 = await Child.create({ parentId: parent3.id });

    // Query children with inherited ordering
    const query = Child.findAll({
      include: [{
        model: Parent,
        required: true
      }]
    });

    // Get the SQL query to inspect ordering
    const sql = query.toString();
    
    // The query should contain ORDER BY with DESC for the parent's primary key
    // This tests the equivalent of Django's inherited model ordering issue
    expect(sql).toMatch(/ORDER BY.*DESC/i);
    expect(sql).not.toMatch(/ORDER BY.*ASC/i);
    
    // Execute query and verify results are in descending order
    const results = await query;
    
    // Verify that results are ordered by parent id in descending order
    for (let i = 0; i < results.length - 1; i++) {
      expect(results[i].Parent.id).toBeGreaterThanOrEqual(results[i + 1].Parent.id);
    }
  });

  it('should preserve negative pk ordering in inherited model queries', () => {
    // Test the specific case mentioned in the Django issue
    // where "-pk" ordering should result in DESC, not ASC
    
    const childQuery = Child.findAll({
      include: [{
        model: Parent,
        required: true
      }],
      order: [['id', 'DESC']] // Simulate inherited "-pk" ordering
    });

    const sql = childQuery.toString();
    
    // Verify that the SQL contains DESC ordering, not ASC
    expect(sql).toMatch(/ORDER BY.*"Child"."id".*DESC/i);
    expect(sql).not.toMatch(/ORDER BY.*"Child"."id".*ASC/i);
  });

  it('should handle complex inheritance ordering scenarios', async () => {
    // Test more complex scenarios similar to Django's model inheritance
    const complexQuery = Child.findAll({
      include: [{
        model: Parent,
        required: true,
        order: [['id', 'DESC']] // Parent's ordering should be preserved
      }],
      order: [['parentId', 'DESC']] // Child's own ordering
    });

    const sql = complexQuery.toString();
    
    // Should contain both orderings with DESC
    expect(sql).toMatch(/ORDER BY/i);
    expect(sql).toMatch(/DESC/i);
    
    // Execute to ensure it works
    const results = await complexQuery;
    expect(Array.isArray(results)).toBe(true);
  });
});
