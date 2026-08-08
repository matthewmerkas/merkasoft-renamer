from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex


class FileListModel(QAbstractListModel):
    FileNameRole = Qt.UserRole + 1
    IsSelectedRole = Qt.UserRole + 2
    IsEvenRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._selected_indices = set()

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None

        row = index.row()
        if role == Qt.DisplayRole or role == self.FileNameRole:
            return self._items[row]
        elif role == self.IsSelectedRole:
            return row in self._selected_indices
        elif role == self.IsEvenRole:
            return row % 2 == 1
        return None

    def roleNames(self):
        return {
            Qt.DisplayRole: b"fileName",
            self.FileNameRole: b"fileName",
            self.IsSelectedRole: b"isSelected",
            self.IsEvenRole: b"isEven"
        }

    def set_items(self, new_items):
        self.beginResetModel()
        self._items = list(new_items)
        self.endResetModel()

    def add_items(self, new_items):
        if not new_items:
            return
        start_row = len(self._items)
        end_row = start_row + len(new_items) - 1

        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self._items.extend(new_items)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self._items.clear()
        self._selected_indices.clear()
        self.endResetModel()

    def remove_indices(self, indices_to_remove):
        if not indices_to_remove:
            return

        for idx in sorted(indices_to_remove, reverse=True):
            if 0 <= idx < len(self._items):
                self.beginRemoveRows(QModelIndex(), idx, idx)
                del self._items[idx]
                self.endRemoveRows()

    def set_selected_indices(self, selected_indices):
        self._selected_indices = set(selected_indices)
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, 0),
                [self.IsSelectedRole]
            )

    @property
    def items(self):
        return self._items
