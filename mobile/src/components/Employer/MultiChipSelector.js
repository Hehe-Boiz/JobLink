import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const MultiChipSelector = ({ label, data, selectedIds = [], onToggle }) => {
    return (
        <View style={{ marginBottom: 20 }}>
            {label && <Text style={styles.label}>{label}</Text>}
            
            <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
                {data.map((item) => {
                    const isSelected = selectedIds.includes(item.id);
                    return (
                        <TouchableOpacity
                            key={item.id}
                            onPress={() => onToggle(item.id)}
                            style={[
                                styles.chip,
                                isSelected && styles.chipActive
                            ]}
                        >
                            <Text style={[
                                styles.text,
                                isSelected && styles.textActive
                            ]}>
                                {item.name}
                            </Text>
                        </TouchableOpacity>
                    );
                })}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: '#524B6B',
        marginBottom: 10,
        marginLeft: 2,
    },
    chip: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 20,
        backgroundColor: '#F5F7FA',
        marginRight: 10,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#EAEAEA'
    },
    chipActive: {
        backgroundColor: '#130160',
        borderColor: '#130160'
    },
    text: {
        color: '#524B6B',
        fontSize: 13
    },
    textActive: {
        color: 'white',
        fontWeight: 'bold'
    }
});

export default MultiChipSelector;