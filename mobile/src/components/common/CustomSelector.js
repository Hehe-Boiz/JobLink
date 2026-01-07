import React, {useState, useRef} from 'react';
import {
    View,
    TouchableOpacity,
    Modal,
    FlatList,
    StyleSheet,
    TouchableWithoutFeedback,
    PanResponder,
    Animated,
    Dimensions
} from 'react-native';
import {TextInput, useTheme} from 'react-native-paper';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from './CustomText';

const {height: screenHeight} = Dimensions.get('window');

const CustomSelector = ({label, placeholder, data, selectedValue, onSelect, required = false}) => {
    const [visible, setVisible] = useState(false);
    const [searchText, setSearchText] = useState('');
    const theme = useTheme();

    const translateY = useRef(new Animated.Value(0)).current;

    const panResponder = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: (_, gesture) => {
                return Math.abs(gesture.dy) > Math.abs(gesture.dx);
            },
            onPanResponderMove: (_, gesture) => {
                if (gesture.dy > 0) {
                    translateY.setValue(gesture.dy);
                }
            },
            onPanResponderRelease: (_, gesture) => {
                if (gesture.dy > 100) {
                    Animated.timing(translateY, {
                        toValue: screenHeight,
                        duration: 200,
                        useNativeDriver: true,
                    }).start(() => {
                        setVisible(false);
                        translateY.setValue(0);
                        setSearchText('');
                    });
                } else {
                    Animated.spring(translateY, {
                        toValue: 0,
                        useNativeDriver: true,
                        tension: 100,
                        friction: 10,
                    }).start();
                }
            },
        })
    ).current;

    const openModal = () => {
        translateY.setValue(0);
        setVisible(true);
    };

    const closeModal = () => {
        Animated.timing(translateY, {
            toValue: screenHeight,
            duration: 200,
            useNativeDriver: true,
        }).start(() => {
            setVisible(false);
            translateY.setValue(0);
            setSearchText('');
        });
    };

    const filteredData = data.filter(item =>
        item.name.toLowerCase().includes(searchText.toLowerCase())
    );

    const selectedItemName = selectedValue?.name;

    const handleSelect = (item) => {
        if (selectedValue?.id === item.id) {
            onSelect(null);
        } else {
            onSelect(item);
        }
        closeModal();
    };

    return (
        <View style={styles.container}>
            {label && (
                <CustomText style={styles.label}>
                    {label} {required && <CustomText style={{color: 'red'}}>*</CustomText>}
                </CustomText>
            )}

            <TouchableOpacity
                style={styles.selectorBox}
                onPress={openModal}
                activeOpacity={0.7}
            >
                <CustomText style={[styles.valueText, !selectedValue && styles.placeholder]}>
                    {selectedItemName || placeholder || "Chạm để chọn..."}
                </CustomText>
                <MaterialCommunityIcons name="chevron-down" size={24} color="#AAA6B9"/>
            </TouchableOpacity>

            <Modal
                visible={visible}
                animationType="slide"
                transparent={true}
                onRequestClose={closeModal}
            >
                <TouchableWithoutFeedback onPress={closeModal}>
                    <View style={styles.modalOverlay}>
                        <TouchableWithoutFeedback>
                            <Animated.View
                                style={[
                                    styles.modalContent,
                                    {transform: [{translateY: translateY}]}
                                ]}
                            >
                                <View
                                    style={styles.handleBarContainer}
                                    {...panResponder.panHandlers}
                                >
                                    <View style={styles.handleBar}/>
                                </View>

                                <View style={styles.modalHeader}>
                                    <CustomText style={styles.modalTitle}>Chọn {label}</CustomText>
                                    <TouchableOpacity onPress={closeModal}>
                                        <MaterialCommunityIcons name="close-circle-outline" size={28} color="#AAA6B9"/>
                                    </TouchableOpacity>
                                </View>

                                <View style={styles.searchContainer}>
                                    <TextInput
                                        mode="outlined"
                                        placeholder="Tìm kiếm..."
                                        value={searchText}
                                        onChangeText={setSearchText}
                                        style={styles.searchInput}
                                        outlineColor="#EAEAEA"
                                        activeOutlineColor="#130160"
                                        left={<TextInput.Icon icon="magnify" color="#AAA6B9"/>}
                                        theme={{roundness: 12}}
                                    />
                                </View>

                                <FlatList
                                    data={filteredData}
                                    keyExtractor={(item) => item.id.toString()}
                                    contentContainerStyle={styles.listContent}
                                    renderItem={({item}) => {
                                        const isSelected = selectedValue?.id === item.id;
                                        return (
                                            <TouchableOpacity
                                                style={[styles.item, isSelected && styles.itemSelected]}
                                                onPress={() => handleSelect(item)}
                                            >
                                                <CustomText
                                                    style={[styles.itemText, isSelected && styles.itemTextSelected]}>
                                                    {item.name}
                                                </CustomText>
                                                {isSelected && <MaterialCommunityIcons name="check-circle" size={22}
                                                                                       color="#130160"/>}
                                            </TouchableOpacity>
                                        );
                                    }}
                                    ItemSeparatorComponent={() => <View style={{height: 10}}/>}
                                    ListEmptyComponent={
                                        <CustomText style={styles.emptyText}>Không tìm thấy kết quả.</CustomText>
                                    }
                                />
                            </Animated.View>
                        </TouchableWithoutFeedback>
                    </View>
                </TouchableWithoutFeedback>
            </Modal>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        marginBottom: 15
    },
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: '#524B6B',
        marginBottom: 8
    },
    selectorBox: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#EAEAEA',
        borderRadius: 15,
        height: 55,
        paddingHorizontal: 20,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: {width: 0, height: 2},
        shadowOpacity: 0.05,
        shadowRadius: 5
    },
    valueText: {
        fontSize: 14,
        color: '#130160',
        fontWeight: '500'
    },
    placeholder: {
        color: '#AAA6B9'
    },

    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'flex-end',
    },
    modalContent: {
        backgroundColor: '#FFFFFF',
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        height: '80%',
        paddingTop: 10,
        paddingBottom: 20,
    },

    handleBarContainer: {
        alignItems: 'center',
        paddingVertical: 15,
        paddingHorizontal: 50,
    },
    handleBar: {
        width: 40,
        height: 5,
        backgroundColor: '#E0E0E0',
        borderRadius: 3,
    },

    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        marginBottom: 15,
    },
    modalTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#130160'
    },
    searchContainer: {
        paddingHorizontal: 20,
        marginBottom: 15
    },
    searchInput: {
        backgroundColor: 'white',
        height: 45,
        fontSize: 14
    },
    listContent: {
        paddingHorizontal: 20,
        paddingBottom: 40,
    },
    item: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 15,
        paddingHorizontal: 15,
        borderRadius: 12,
        backgroundColor: '#F9F9F9',
        borderWidth: 1,
        borderColor: 'transparent'
    },
    itemSelected: {
        backgroundColor: '#F3F0FF',
        borderColor: '#130160',
    },
    itemText: {
        fontSize: 15,
        color: '#524B6B'
    },
    itemTextSelected: {
        color: '#130160',
        fontWeight: 'bold'
    },
    emptyText: {
        textAlign: 'center',
        color: '#999',
        marginTop: 20
    },
});

export default CustomSelector;