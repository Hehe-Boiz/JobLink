import React, {useState} from 'react';
import {
    View,
    FlatList,
    TouchableOpacity,
    StyleSheet,
    Alert,
    Image,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import ConfirmationSheet from "../../components/common/ConfirmationSheet";

import CustomText from '../../components/common/CustomText';
import CustomHeader from '../../components/common/CustomHeader';

const ALL_LANGUAGES = [
    {id: 'id', name: 'Indonesian', flag: 'https://flagcdn.com/w160/id.png'},
    {id: 'en', name: 'English', flag: 'https://flagcdn.com/w160/gb.png'},
    {id: 'ar', name: 'Arabic', flag: 'https://flagcdn.com/w160/sa.png'},
    {id: 'my', name: 'Malaysian', flag: 'https://flagcdn.com/w160/my.png'},
    {id: 'fr', name: 'French', flag: 'https://flagcdn.com/w160/fr.png'},
    {id: 'de', name: 'German', flag: 'https://flagcdn.com/w160/de.png'},
];

const LanguageList = ({navigation}) => {
    const [userLanguages, setUserLanguages] = useState([
        {...ALL_LANGUAGES[0], isFirst: true, oral: 10, written: 10},
        {...ALL_LANGUAGES[1], isFirst: false, oral: 8, written: 8},
    ]);
    const [removeVisible, setRemoveVisible] = useState(false);
    const [pendingRemove, setPendingRemove] = useState(null);

    const handleDeletePress = (item) => {
        setPendingRemove(item);
        setRemoveVisible(true);
    };

    const handleDelete = (id) => {
        Alert.alert(
            'Remove Language?',
            'Are you sure you want to delete this language?',
            [
                {text: 'Cancel', style: 'cancel'},
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: () => setUserLanguages((prev) => prev.filter((l) => l.id !== id)),
                },
            ]
        );
    };

    const updateLanguage = (updatedLang) => {
        setUserLanguages((prev) => prev.map((l) => (l.id === updatedLang.id ? updatedLang : l)));
    };

    const addNewLanguage = (newLang) => {
        if (!userLanguages.find((l) => l.id === newLang.id)) {
            setUserLanguages((prev) => [
                ...prev,
                {...newLang, isFirst: false, oral: 1, written: 1},
            ]);
        }
    };

    const renderItem = ({item}) => {
        return (
            <TouchableOpacity
                activeOpacity={0.9}
                style={styles.card}
                onPress={() =>
                    navigation.navigate('LanguageDetail', {
                        language: item,
                        onSave: updateLanguage,
                    })
                }
            >
                <View style={styles.cardHeader}>
                    <View style={styles.leftRow}>
                        <View style={styles.flagWrap}>
                            <Image source={{uri: item.flag}} style={styles.flagImage}/>
                        </View>

                        <View style={{flexShrink: 1}}>
                            <View style={styles.nameRow}>
                                <CustomText style={styles.langName}>{item.name}</CustomText>
                                {item.isFirst ? (
                                    <CustomText style={styles.firstLangNote}>(First language)</CustomText>
                                ) : null}
                            </View>
                        </View>
                    </View>

                    <TouchableOpacity
                        hitSlop={{top: 10, bottom: 10, left: 10, right: 10}}
                        onPress={() => handleDeletePress(item)}
                    >
                        <MaterialCommunityIcons name="trash-can-outline" size={24} color="#FF3B30"/>
                    </TouchableOpacity>
                </View>

                <View style={styles.levels}>
                    <CustomText style={styles.levelText}>Oral : Level {item.oral}</CustomText>
                    <CustomText style={styles.levelText}>Written : Level {item.written}</CustomText>
                </View>
            </TouchableOpacity>
        );
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <CustomHeader navigation={navigation} title=""/>

            <View style={styles.subHeader}>
                <CustomText style={styles.headerTitle}>Language</CustomText>

                <TouchableOpacity
                    activeOpacity={0.8}
                    onPress={() =>
                        navigation.navigate('AddLanguage', {
                            onSelect: addNewLanguage,
                            existingIds: userLanguages.map(l => l.id),
                        })
                    }

                >
                    <View style={styles.addRow}>
                        <CustomText style={styles.addText}>Add</CustomText>
                        <View style={styles.addCircle}>
                            <MaterialCommunityIcons name="plus" size={18} color="#6A5ACD"/>
                        </View>
                    </View>
                </TouchableOpacity>
            </View>

            <FlatList
                data={userLanguages}
                renderItem={renderItem}
                keyExtractor={(item) => item.id}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
            />

            <View style={styles.footer}>
                <TouchableOpacity activeOpacity={0.9} style={styles.saveButton}>
                    <CustomText style={styles.saveButtonText}>SAVE</CustomText>
                </TouchableOpacity>
            </View>
            <ConfirmationSheet
                visible={removeVisible}
                type="remove_language"
                entityName={pendingRemove?.name}
                onClose={() => {
                    setRemoveVisible(false);
                    setPendingRemove(null);
                }}
                onConfirm={() => {
                    if (pendingRemove) {
                        setUserLanguages(prev => prev.filter(l => l.id !== pendingRemove.id));
                    }
                    setRemoveVisible(false);
                    setPendingRemove(null);
                }}
            />

        </SafeAreaView>

    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9'
    },

    subHeader: {
        paddingHorizontal: 22,
        paddingTop: 6,
        paddingBottom: 10,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    headerTitle: {
        fontSize: 22,
        fontWeight: '800',
        color: '#14121F',
    },

    addRow: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    addText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#6A5ACD',
        marginRight: 10,
    },
    addCircle: {
        width: 30,
        height: 30,
        borderRadius: 15,
        backgroundColor: '#EDEAFF',
        alignItems: 'center',
        justifyContent: 'center',
    },

    listContent: {
        paddingHorizontal: 18,
        paddingTop: 8,
        paddingBottom: 110,
        marginTop: 20,
    },

    card: {
        backgroundColor: '#FFFFFF',
        borderRadius: 18,
        paddingVertical: 16,
        paddingHorizontal: 16,
        marginBottom: 14,

        shadowColor: '#000',
        shadowOpacity: 0.06,
        shadowRadius: 10,
        shadowOffset: {width: 0, height: 6},
        elevation: 2,
    },

    cardHeader: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
    },

    leftRow: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1
    },

    flagWrap: {
        width: 34,
        height: 34,
        borderRadius: 17,
        overflow: 'hidden',
        marginRight: 12,
        borderWidth: 1,
        borderColor: '#EFEFF5',
        backgroundColor: '#FFF',
    },
    flagImage: {
        width: '100%',
        height: '100%'
    },

    nameRow: {
        flexDirection: 'row',
        alignItems: 'center',
        flexWrap: 'wrap'
    },
    langName: {
        fontSize: 16,
        fontWeight: '800',
        color: '#14121F',
        marginRight: 6
    },
    firstLangNote: {
        fontSize: 13,
        color: '#3B3B3B',
        fontWeight: '600'
    },

    levels: {
        marginTop: 15,
        paddingLeft: 5
    },
    levelText: {
        fontSize: 15,
        color: '#A8A8B2',
        marginBottom: 10,
        fontWeight: '500'
    },

    footer: {
        position: 'absolute',
        left: 18,
        right: 18,
        bottom: 25,
    },
    saveButton: {
        backgroundColor: '#120D3F',
        borderRadius: 12,
        paddingVertical: 16,
        alignItems: 'center',
        justifyContent: 'center',
    },
    saveButtonText: {
        color: '#FFFFFF',
        fontWeight: '800',
        fontSize: 16
    },
});

export default LanguageList;
