# Adding a New Component to the Dashboard System

This guide explains the steps required to make an existing React component available as a draggable item in the dashboard editor.

## Architecture Overview

The dashboard system uses:
- **Backend**: Django models with polymorphic inheritance for component-specific data
- **Frontend**: GridStack for drag-and-drop layout + React components for rendering

## Steps Required

### 1. Backend: Create Model

**File**: `backend/api/models.py`

Create a new model that extends `DashboardComponent`. Add any component-specific fields that need to be persisted.

```python
class MyNewComponent(DashboardComponent):
    # Add component-specific fields
    my_field = models.CharField(max_length=100, default="")
```

The base `DashboardComponent` class provides:
- `dashboard` - ForeignKey to the parent Dashboard
- `x`, `y`, `w`, `h` - GridStack layout coordinates
- `component_name` - String matching the React componentMap key
- `order` - Z-order for layering

### 2. Backend: Create Serializer

**File**: `backend/api/serializers.py`

Create a serializer extending `DashboardComponentSerializer`:

```python
class MyNewComponentSerializer(DashboardComponentSerializer):
    class Meta:
        model = MyNewComponent
        fields = "__all__"
```

Add the mapping to `DashboardComponentPolymorphicSerializer`:

```python
class DashboardComponentPolymorphicSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        DashboardComponent: DashboardComponentSerializer,
        # ... existing components ...
        MyNewComponent: MyNewComponentSerializer,  # Add this line
    }
```

### 3. Backend: Update Views

**File**: `backend/api/views.py`

Update the `get_layout` method to cast base components to your new type:

```python
@action(detail=True, methods=["GET"])
def get_layout(self, request, pk=None):
    # ... existing code ...
    for comp in base_components:
        # ... existing conditions ...
        elif comp.component_name == 'MyNewComponent':
            components.append(MyNewComponent.objects.get(id=comp.id))
        else:
            components.append(comp)
```

Update the `save_layout` method to create instances of your new type:

```python
@action(detail=True, methods=["POST"])
def save_layout(self, request, pk=None):
    # ... existing code ...
    for item in layout:
        component_name = item['component_name']
        # ... existing conditions ...
        elif component_name == 'MyNewComponent':
            MyNewComponent.objects.create(
                dashboard=dashboard,
                x=item['x'],
                y=item['y'],
                w=item['w'],
                h=item['h'],
                component_name=component_name,
                my_field=item.get('my_field', ''),  # Component-specific fields
            )
```

Don't forget to import your new model at the top of views.py.

### 4. Frontend: Create/Adapt Component

**File**: `frontend/src/components/componentMap.tsx`

Create a wrapper component implementing the `ComponentProps` interface:

```typescript
interface ComponentProps {
  node: GridStackNode & {
    component_name?: string;
    // Add your component-specific fields here
  };
  onUpdate?: (updates: Partial<GridStackNode>) => void;
  isEditMode?: boolean;
  selectedFile?: any;  // Available if your component needs file context
}

const MyNewComponent: React.FC<ComponentProps> = ({ node, onUpdate, isEditMode = false, selectedFile }) => {
  return (
    <Card className="w-full h-full rounded-none">
      <CardContent>
        {isEditMode ? (
          // Edit mode UI
          <div>Edit Mode</div>
        ) : (
          // View mode UI
          <div>View Mode</div>
        )}
      </CardContent>
    </Card>
  );
};
```

Add your component to the `componentMap` export:

```typescript
export const componentMap: Record<string, React.FC<ComponentProps>> = {
  TextBoxComponent,
  NumberOfEventsComponent,
  ImageComponent,
  MyNewComponent,  // Add this line
};
```

### 5. Frontend: Add to Side Panel

**File**: `frontend/src/gridstack/lib/sidepanel.tsx`

Add `GridStack.setupDragIn()` configuration in the `useEffect`:

```typescript
GridStack.setupDragIn(
  ".sidepanel .my-new-component",
  {
    helper: "clone",
    appendTo: "body",
  },
  [{
    h: 2,           // Default height in grid units
    w: 2,           // Default width in grid units
    content: "My New Component",
    component_name: "MyNewComponent",
    order: 0
    // Add default values for component-specific fields
  }]
);
```

Add the draggable UI element in the return JSX:

```tsx
<div className="grid-stack-item sidepanel-item my-new-component flex flex-col justify-center items-center border p-2 m-2 gap-2 rounded-md text-sm font-medium hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50">
  <img src="src/images/my-component.png" width="100" height="50"/>
  <div>My New Component</div>
</div>
```

### 6. Run Migrations

After creating the backend model, create and apply migrations:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

---

## Adding Configurable Properties

If your component needs properties that users can configure in edit mode (like settings, options, or parameters), follow these additional steps. This section uses `VariantsComponent` as an example, which has two configurable properties: `automatic_loading` (boolean) and `leading_object_type` (string).

### 1. Backend: Add Fields to Model

**File**: `backend/api/models.py`

Add the configurable fields to your component model:

```python
class VariantsComponent(DashboardComponent):
    automatic_loading = models.BooleanField(default=False, null=True, blank=True)
    leading_object_type = models.CharField(max_length=100, null=True, blank=True)
```

**Tips:**
- Use `null=True, blank=True` for optional fields
- The serializer with `fields = "__all__"` will automatically include these fields

### 2. Backend: Update save_layout

**File**: `backend/api/views.py`

Update the `save_layout` method to read and store the new fields:

```python
elif component_name == 'VariantsComponent':
    VariantsComponent.objects.create(
        dashboard=dashboard,
        x=item['x'],
        y=item['y'],
        w=item['w'],
        h=item['h'],
        component_name=component_name,
        automatic_loading=item.get('automatic_loading', False),
        leading_object_type=item.get('leading_object_type', ''),
    )
```

### 3. Frontend: Update ComponentProps Interface

**File**: `frontend/src/components/componentMap.tsx`

Add your new properties to the node interface:

```typescript
interface ComponentProps {
  node: GridStackNode & {
    component_name?: string;
    // ... existing fields ...
    automatic_loading?: boolean;      // Your new fields
    leading_object_type?: string;
  };
  onUpdate?: (updates: Partial<GridStackNode>) => void;
  isEditMode?: boolean;
  selectedFile?: { id: number; [key: string]: any };
}
```

### 4. Frontend: Create Component with Edit/View Modes

**File**: `frontend/src/components/componentMap.tsx`

Create a component that shows a configuration form in edit mode and the actual component in view mode:

```typescript
const VariantsComponent: React.FC<ComponentProps> = ({
  node,
  onUpdate,
  isEditMode = false,
  selectedFile
}) => {
  // Local state for form values (initialized from node)
  const [automaticLoading, setAutomaticLoading] = useState(node.automatic_loading ?? false);
  const [leadingType, setLeadingType] = useState(node.leading_object_type ?? '');

  // Sync local state when node changes (e.g., after loading)
  useEffect(() => {
    setAutomaticLoading(node.automatic_loading ?? false);
    setLeadingType(node.leading_object_type ?? '');
  }, [node.automatic_loading, node.leading_object_type]);

  // Handler that updates both local state AND calls onUpdate
  const handleAutomaticLoadingChange = (checked: boolean) => {
    setAutomaticLoading(checked);
    onUpdate?.({ automatic_loading: checked } as any);  // Cast needed for custom props
  };

  const handleLeadingTypeChange = (value: string) => {
    setLeadingType(value);
    onUpdate?.({ leading_object_type: value } as any);
  };

  if (isEditMode) {
    // EDIT MODE: Show configuration form
    return (
      <Card className="w-full h-full rounded-none">
        <CardHeader>
          <CardTitle>Component Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>Automatic loading</Label>
            <Switch
              checked={automaticLoading}
              onCheckedChange={handleAutomaticLoadingChange}
            />
          </div>
          {/* Add more form fields as needed */}
        </CardContent>
      </Card>
    );
  }

  // VIEW MODE: Render the actual component with stored settings
  return (
    <Card className="w-full h-full rounded-none overflow-auto">
      <CardContent className="p-0 h-full">
        <YourActualComponent
          automaticLoading={automaticLoading}
          leadingType={leadingType}
          // ... other props
        />
      </CardContent>
    </Card>
  );
};
```

**Key Points:**
- Initialize local state from `node` properties
- Use `useEffect` to sync when node changes
- Call `onUpdate()` with your custom properties (cast to `any` since they're not in `GridStackNode`)
- The `onUpdate` callback updates the GridStackNode object in memory

### 5. Frontend: Update GridStackProvider (Critical!)

**File**: `frontend/src/gridstack/lib/gridstackprovider.tsx`

This is the most important step! You must update three places:

#### 5a. Update `getLayout()` to extract your properties

Add handling for your component in the `getLayout()` function:

```typescript
const getLayout = () => {
  // ... existing code ...
  return nodes.map((node, index) => {
    let props: any = {};

    if (component_name === "TextBoxComponent") {
      props = { text: (node as any).text || "", font_size: 14 };
    } else if (component_name === "VariantsComponent") {
      // ADD THIS: Extract your component's properties
      props = {
        automatic_loading: (node as any).automatic_loading ?? false,
        leading_object_type: (node as any).leading_object_type ?? '',
      };
    }
    // ... rest of function
  });
};
```

#### 5b. Update `loadLayout()` to pass properties to `addWidget()`

When adding widgets, include all custom properties so they're available when the component renders:

```typescript
const widgetEl = gridRef.current?.addWidget({
  x: item.x,
  y: item.y,
  w: item.w,
  h: item.h,
  content,
  component_name: item.component_name,
  text: item.text,
  color: item.color,
  font_size: item.font_size,
  image: item.image,
  automatic_loading: item.automatic_loading,      // ADD your fields
  leading_object_type: item.leading_object_type,  // ADD your fields
});
```

#### 5c. Update `loadLayout()` to assign properties to the node

After adding the widget, also assign properties to the node object:

```typescript
if (node) {
  (node as any).component_name = item.component_name;
  (node as any).text = item.text;
  // ... existing assignments ...
  (node as any).automatic_loading = item.automatic_loading;      // ADD
  (node as any).leading_object_type = item.leading_object_type;  // ADD
}
```

### 6. Frontend: Update Side Panel Defaults

**File**: `frontend/src/gridstack/lib/sidepanel.tsx`

Add default values for your properties in the drag-in configuration:

```typescript
GridStack.setupDragIn(
  ".sidepanel .variants-component",
  { helper: "clone", appendTo: "body" },
  [{
    h: 4,
    w: 6,
    content: "Variants Explorer",
    component_name: "VariantsComponent",
    automatic_loading: false,        // Default value
    leading_object_type: '',         // Default value
    order: 0
  }]
);
```

### 7. Run Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

---

## Data Flow Summary

Understanding the complete data flow helps debug persistence issues:

```
┌─ SAVE PATH ──────────────────────────────────────────┐
│                                                       │
│  User changes setting in edit mode                   │
│          ↓                                           │
│  Component calls onUpdate({ my_prop: value })        │
│          ↓                                           │
│  GridProvider: Object.assign(node, updates)          │
│          ↓                                           │
│  User clicks Save button                             │
│          ↓                                           │
│  getLayout() extracts properties from node           │
│          ↓                                           │
│  saveLayout() API call with layout array             │
│          ↓                                           │
│  Backend save_layout creates component with fields   │
│          ↓                                           │
│  Database stores the values                          │
│                                                       │
└───────────────────────────────────────────────────────┘

┌─ LOAD PATH ──────────────────────────────────────────┐
│                                                       │
│  User selects dashboard                              │
│          ↓                                           │
│  getLayout() API returns component data              │
│          ↓                                           │
│  loadLayout() calls addWidget() WITH properties      │
│          ↓                                           │
│  GridStack triggers renderCB immediately             │
│          ↓                                           │
│  Component receives node with properties             │
│          ↓                                           │
│  Component initializes state from node               │
│          ↓                                           │
│  UI displays with loaded configuration               │
│                                                       │
└───────────────────────────────────────────────────────┘
```

**Important:** Properties must be passed to `addWidget()` because GridStack calls `renderCB` immediately. If you only assign properties to the node after `addWidget()`, the component will render before the properties are available.

---

## Tips

- **Component Size**: Consider the complexity of your component when setting default `h` and `w` values. Complex components may need larger defaults.
- **Edit Mode**: Use `isEditMode` prop to show different UI for editing vs viewing.
- **File Context**: If your component needs access to the selected event log file, use the `selectedFile` prop.
- **State Persistence**: Only data stored in the backend model will persist. UI state like zoom levels should be stored locally or as model fields.
- **Image Assets**: Place thumbnail images in `frontend/src/images/` for the side panel.
- **Type Casting**: When calling `onUpdate()` with custom properties, cast to `any` since they're not part of the standard `GridStackNode` type.

## Existing Components

For reference, see these existing implementations:
- `TextBoxComponent` - Simple text storage and display
- `NumberOfEventsComponent` - Fetches data based on selected file
- `ImageComponent` - Handles file uploads
- `VariantsComponent` - Complex component with configurable properties and embedded React component
