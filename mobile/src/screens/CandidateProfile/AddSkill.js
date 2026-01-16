import React, {useState, useEffect} from 'react';
import {
    View,
    TouchableOpacity,
    TextInput,
    ScrollView,
    StyleSheet,
    Keyboard, ActivityIndicator, FlatList, TouchableWithoutFeedback
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import SkillChip from '../../components/common/SkillChip';
import {authApis, endpoints} from '../../utils/Apis';
import AsyncStorage from "@react-native-async-storage/async-storage";

const AddSkill = ({navigation, route}) => {
    const existingSkills = route?.params?.skills || [];
    const onSaveCallback = route?.params?.onSave;

    const [hasMore, setHasMore] = useState(true);
    const [searchText, setSearchText] = useState('');
    const [selectedSkills, setSelectedSkills] = useState(existingSkills);
    const [suggestions, setSuggestions] = useState([]);
    const [lastAddedSkill, setLastAddedSkill] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [isFocused, setIsFocused] = useState(false);

    const fetchSkills = async (pageNumber, reset = false) => {
        if (isLoading) return;
        setIsLoading(true);

        try {
            const token = await AsyncStorage.getItem('token');
            let url = `${endpoints.skills}?page=${pageNumber}`;
            if (searchText) {
                url += `&search=${searchText}`;
            }
            const res = await authApis(token).get(url);

            const newSkills = res.data.results.map(item => item.name);

            if (reset) {
                setSuggestions(newSkills);
            } else {
                setSuggestions(prev => [...prev, ...newSkills]);
            }

            setHasMore(res.data.next !== null);

        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (searchText.trim() === '') {
            if (isFocused) {
                fetchSkills(1, true);
            } else {
                setSuggestions([]);
            }
            return;
        }
        setPage(1);
        const timer = setTimeout(() => {
            fetchSkills(1, true);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchText, isFocused]);

    const handleFocus = () => {
        setIsFocused(true);
        if (searchText === '') {
            fetchSkills(1, true);
        }
    };

    const handleBlur = () => {
        setIsFocused(false);
        if (searchText === '') {
            setSuggestions([]);
        }
    };

    const handleLoadMore = () => {
        if (hasMore && !isLoading) {
            const nextPage = page + 1;
            setPage(nextPage);
            fetchSkills(nextPage, false);
        }
    };

    const handleSelectSkill = (skill) => {
        if (!selectedSkills.includes(skill)) {
            setSelectedSkills([...selectedSkills, skill]);
            setLastAddedSkill(skill);
        }
        setSearchText('');
        Keyboard.dismiss();
    };

    const handleRemoveSkill = (skillToRemove) => {
        setSelectedSkills(selectedSkills.filter(skill => skill !== skillToRemove));
        if (lastAddedSkill === skillToRemove) {
            setLastAddedSkill(null);
        }
    };

    const handleClearSearch = () => {
        setSearchText('');
        setSuggestions([]);
    };

    const handleSave = async () => {
        try {
            const token = await AsyncStorage.getItem('token');

            await authApis(token).patch(endpoints.candidate_profile, {
                skills: selectedSkills
            });
            if (onSaveCallback) {
                onSaveCallback(selectedSkills);
            }
            navigation.goBack();

        } catch (error) {
            console.error("Lỗi save skill:", error);
            alert("Lỗi cập nhật kỹ năng!");
        }
    };

    const handleBack = () => {
        navigation.goBack();
    };

    const renderItem = ({item}) => (
        <TouchableOpacity
            style={styles.suggestionItem}
            onPress={() => handleSelectSkill(item)}
        >
            <CustomText style={styles.suggestionText}>{item}</CustomText>
        </TouchableOpacity>
    );

    const renderFooter = () => {
        if (!isLoading) return null;
        return <ActivityIndicator size="small" color="#130160" style={{margin: 10}}/>;
    };

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            <View style={styles.header}>
                <TouchableOpacity onPress={handleBack} style={styles.backButton}>
                    <MaterialCommunityIcons name="arrow-left" size={24} color="#150B3D"/>
                </TouchableOpacity>
            </View>
            <TouchableWithoutFeedback onPress={() => {
                Keyboard.dismiss();
                setIsFocused(false);
            }}>
                <View style={styles.content}>
                    <CustomText style={styles.title}>Add Skill</CustomText>

                    <View style={styles.searchContainer}>
                        <MaterialCommunityIcons name="magnify" size={22} color="#AAA6B9"/>
                        <TextInput
                            style={styles.searchInput}
                            value={searchText}
                            onChangeText={setSearchText}
                            placeholder="Search skills"
                            placeholderTextColor="#AAA6B9"
                            onFocus={handleFocus}
                            onBlur={handleBlur}
                        />
                        {searchText.length > 0 && (
                            <TouchableOpacity onPress={handleClearSearch}>
                                <MaterialCommunityIcons name="close" size={20} color="#AAA6B9"/>
                            </TouchableOpacity>
                        )}
                    </View>

                    {(suggestions.length > 0 || isFocused) && (
                        <FlatList
                            data={suggestions}
                            renderItem={renderItem}
                            keyExtractor={(item, index) => index.toString()}
                            onEndReached={handleLoadMore}
                            onEndReachedThreshold={0.5}
                            ListFooterComponent={renderFooter}
                            showsVerticalScrollIndicator={false}
                            keyboardShouldPersistTaps="handled"
                            initialNumToRender={20}
                            maxToRenderPerBatch={20}
                            windowSize={5}
                            removeClippedSubviews={true}
                        />
                    )}

                    {suggestions.length === 0 && selectedSkills.length > 0 && (
                        <View style={styles.chipsContainer}>
                            <View style={styles.chipsWrapper}>
                                {selectedSkills.map((skill, index) => {
                                    const isLastAdded = skill === lastAddedSkill;
                                    return (
                                        <SkillChip
                                            key={index}
                                            label={skill}
                                            onRemove={() => handleRemoveSkill(skill)}
                                            isHighlighted={isLastAdded} // SkillChip đã hỗ trợ prop này
                                            showRemoveIcon={true}
                                        />
                                    );
                                })}
                            </View>
                        </View>
                    )}

                    {/* Save Button */}
                    <View style={styles.buttonContainer}>
                        <TouchableOpacity
                            style={[
                                styles.saveButton,
                                selectedSkills.length === 0 && styles.saveButtonDisabled,
                            ]}
                            onPress={handleSave}
                            disabled={selectedSkills.length === 0}
                            activeOpacity={0.8}
                        >
                            <CustomText style={styles.saveButtonText}>SAVE</CustomText>
                        </TouchableOpacity>
                    </View>
                </View>
            </TouchableWithoutFeedback>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9',
    },
    header: {
        paddingHorizontal: 20,
        paddingVertical: 12,
    },
    backButton: {
        width: 40,
        height: 40,
        justifyContent: 'center',
    },
    content: {
        flex: 1,
        paddingHorizontal: 20,
    },
    title: {
        fontSize: 18,
        fontWeight: '700',
        color: '#150B3D',
        marginBottom: 20,
    },
    searchContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#EAEAEA',
        borderRadius: 10,
        paddingHorizontal: 15,
        height: 50,
        marginBottom: 16,
    },
    searchInput: {
        flex: 1,
        marginLeft: 10,
        fontSize: 14,
        color: '#150B3D',
        fontFamily: 'DMSans-Regular',
    },
    suggestionsList: {
        flex: 1,
    },
    suggestionItem: {
        paddingVertical: 14,
        borderBottomWidth: 0,
    },
    suggestionText: {
        fontSize: 14,
        fontWeight: '400',
        color: '#150B3D',
    },
    chipsContainer: {
        flex: 1,
    },
    chipsWrapper: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 10,
    },
    chip: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#EAEAEA',
        borderRadius: 8,
        paddingVertical: 10,
        paddingLeft: 14,
        paddingRight: 10,
        gap: 8,
    },
    chipHighlighted: {
        backgroundColor: '#FCA34D',
        borderColor: '#FCA34D',
    },
    chipText: {
        fontSize: 13,
        fontWeight: '500',
        color: '#524B6B',
    },
    chipTextHighlighted: {
        color: '#FFFFFF',
    },
    buttonContainer: {
        paddingVertical: 18,
    },
    saveButton: {
        backgroundColor: '#130160',
        height: 53,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
    },
    saveButtonDisabled: {
        backgroundColor: '#AAA6B9',
    },
    saveButtonText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#FFFFFF',
    },
});

export default AddSkill;