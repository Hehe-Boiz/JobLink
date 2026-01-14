import React, {useMemo, useState} from 'react';
import {
    View,
    TextInput,
    FlatList,
    TouchableOpacity,
    StyleSheet,
    Image,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import CustomHeader from '../../components/common/CustomHeader';

export const ALL_LANGUAGES = [
    {id: 'ar', name: 'Arabic', flag: 'https://flagcdn.com/w160/sa.png'},
    {id: 'id', name: 'Indonesian', flag: 'https://flagcdn.com/w160/id.png'},
    {id: 'my', name: 'Malaysian', flag: 'https://flagcdn.com/w160/my.png'},
    {id: 'en', name: 'English', flag: 'https://flagcdn.com/w160/gb.png'},
    {id: 'fr', name: 'French', flag: 'https://flagcdn.com/w160/fr.png'},
    {id: 'de', name: 'German', flag: 'https://flagcdn.com/w160/de.png'},
    {id: 'hi', name: 'Hindi', flag: 'https://flagcdn.com/w160/in.png'},
    {id: 'it', name: 'Italian', flag: 'https://flagcdn.com/w160/it.png'},
    {id: 'ja', name: 'Japanese', flag: 'https://flagcdn.com/w160/jp.png'},
    {id: 'ko', name: 'Korean', flag: 'https://flagcdn.com/w160/kr.png'},
];

const AddLanguage = ({navigation, route}) => {
    const [search, setSearch] = useState('');
    const [selectedId, setSelectedId] = useState(null);

    // danh sách ngôn ngữ đã có để show dấu check
    const existingIds = route?.params?.existingIds || [];

    const filtered = useMemo(() => {
        const q = search.trim().toLowerCase();
        if (!q) return ALL_LANGUAGES;
        return ALL_LANGUAGES.filter((l) => l.name.toLowerCase().includes(q));
    }, [search]);

    const handleSelect = (lang) => {
        setSelectedId(lang.id);

        if (route?.params?.onSelect) route.params.onSelect(lang);
        navigation.goBack();
    };

    const renderItem = ({item}) => {
        const isSelected = selectedId === item.id;
        const isExisting = existingIds.includes(item.id);

        return (
            <TouchableOpacity
                activeOpacity={0.9}
                onPress={() => handleSelect(item)}
                style={[styles.row, isSelected && styles.rowSelected]}
            >
                <View style={styles.left}>
                    <View style={styles.flagWrap}>
                        <Image source={{uri: item.flag}} style={styles.flagImg}/>
                    </View>
                    <CustomText style={[styles.name, isSelected && styles.nameSelected]}>
                        {item.name}
                    </CustomText>
                </View>

                {isExisting ? (
                    <MaterialCommunityIcons
                        name="check"
                        size={22}
                        color={isSelected ? '#FFFFFF' : '#1F1F1F'}
                    />
                ) : (
                    <View style={{width: 22}}/>
                )}
            </TouchableOpacity>
        );
    };

    return (
        <SafeAreaView style={styles.container}>
            <CustomHeader navigation={navigation} title=""/>

            <View style={styles.titleWrap}>
                <CustomText style={styles.title}>Add Language</CustomText>
            </View>

            <View style={styles.searchBar}>
                <MaterialCommunityIcons name="magnify" size={20} color="#A8A8B2"/>
                <TextInput
                    value={search}
                    onChangeText={setSearch}
                    placeholder="Search skills"
                    placeholderTextColor="#B7B7C2"
                    style={styles.searchInput}
                />
            </View>

            <FlatList
                data={filtered}
                keyExtractor={(it) => it.id}
                renderItem={renderItem}
                contentContainerStyle={{paddingHorizontal: 18, paddingBottom: 18}}
                ItemSeparatorComponent={() => <View style={{height: 12}}/>}
                showsVerticalScrollIndicator={false}
            />
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9'
    },

    titleWrap: {
        paddingHorizontal: 18,
        paddingTop: 6,
        paddingBottom: 10
    },
    title: {
        fontSize: 22,
        fontWeight: '800',
        color: '#14121F'
    },

    searchBar: {
        marginHorizontal: 18,
        marginBottom: 30,
        height: 55,
        borderRadius: 14,
        paddingHorizontal: 14,
        backgroundColor: '#FFFFFF',
        flexDirection: 'row',
        alignItems: 'center',
        elevation: 1,
        marginTop: 15,
    },
    searchInput: {
        marginLeft: 10,
        flex: 1,
        color: '#14121F'
    },

    row: {
        backgroundColor: '#FFFFFF',
        borderRadius: 16,
        paddingVertical: 14,
        paddingHorizontal: 14,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        elevation: 1,
    },
    rowSelected: {
        backgroundColor: '#A99BFF',
    },
    left: {
        flexDirection: 'row',
        alignItems: 'center'
    },

    flagWrap: {
        width: 34,
        height: 34,
        borderRadius: 17,
        overflow: 'hidden',
        marginRight: 12,
        borderWidth: 1,
        borderColor: '#EFEFF5',
    },
    flagImg: {
        width: '100%',
        height: '100%'
    },

    name: {
        fontSize: 16,
        fontWeight: '500',
        color: '#14121F'
    },
    nameSelected: {
        color: '#FFFFFF'
    },
});

export default AddLanguage;
