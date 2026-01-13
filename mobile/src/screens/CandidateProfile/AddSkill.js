import React, {useState, useEffect} from 'react';
import {
    View,
    TouchableOpacity,
    TextInput,
    ScrollView,
    StyleSheet,
    Keyboard,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import SkillChip from '../../components/common/SkillChip';

const ALL_SKILLS = [
    'Leadership', 'Teamwork', 'Communication', 'Problem Solving',
    'Critical Thinking', 'Time Management', 'Creativity', 'Adaptability',
    'Graphic Design', 'Graphic Thinking', 'UI/UX Design', 'Adobe Indesign',
    'Web Design', 'InDesign', 'Canva Design', 'User Interface Design',
    'Product Design', 'User Experience Design', 'Figma', 'Sketch',
    'JavaScript', 'React', 'React Native', 'Python', 'Java', 'Node.js',
    'Project Management', 'Agile', 'Scrum', 'Data Analysis',
    'Marketing', 'SEO', 'Content Writing', 'Public Speaking',
    'English', 'Vietnamese', 'Japanese', 'Chinese',
    'Responsibility', 'Target oriented', 'Consistent', 'Visioner',
    'Good communication skills', 'Negotiation', 'Decision Making',
];

const AddSkill = ({navigation, route}) => {
    // Nhận skills đã có từ route params
    const existingSkills = route?.params?.skills || [];

    const [searchText, setSearchText] = useState('');
    const [selectedSkills, setSelectedSkills] = useState(existingSkills);
    const [suggestions, setSuggestions] = useState([]);
    const [lastAddedSkill, setLastAddedSkill] = useState(null);

    // Filter suggestions khi search text thay đổi
    useEffect(() => {
        if (searchText.trim()) {
            const filtered = ALL_SKILLS.filter(skill =>
                skill.toLowerCase().includes(searchText.toLowerCase()) &&
                !selectedSkills.includes(skill)
            );
            setSuggestions(filtered);
        } else {
            setSuggestions([]);
        }
    }, [searchText, selectedSkills]);

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

    const handleSave = () => {
        // Trả về skills đã chọn
        if (route?.params?.onSave) {
            route.params.onSave(selectedSkills);
        }
        navigation.goBack();
    };

    const handleBack = () => {
        navigation.goBack();
    };

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={handleBack} style={styles.backButton}>
                    <MaterialCommunityIcons name="arrow-left" size={24} color="#150B3D"/>
                </TouchableOpacity>
            </View>

            <View style={styles.content}>
                {/* Title */}
                <CustomText style={styles.title}>Add Skill</CustomText>

                {/* Search Input */}
                <View style={styles.searchContainer}>
                    <MaterialCommunityIcons name="magnify" size={22} color="#AAA6B9"/>
                    <TextInput
                        style={styles.searchInput}
                        value={searchText}
                        onChangeText={setSearchText}
                        placeholder="Search skills"
                        placeholderTextColor="#AAA6B9"
                    />
                    {searchText.length > 0 && (
                        <TouchableOpacity onPress={handleClearSearch}>
                            <MaterialCommunityIcons name="close" size={20} color="#AAA6B9"/>
                        </TouchableOpacity>
                    )}
                </View>

                {/* Suggestions List (khi đang search) */}
                {suggestions.length > 0 && (
                    <ScrollView
                        style={styles.suggestionsList}
                        showsVerticalScrollIndicator={false}
                        keyboardShouldPersistTaps="handled"
                    >
                        {suggestions.map((skill, index) => (
                            <TouchableOpacity
                                key={index}
                                style={styles.suggestionItem}
                                onPress={() => handleSelectSkill(skill)}
                            >
                                <CustomText style={styles.suggestionText}>{skill}</CustomText>
                            </TouchableOpacity>
                        ))}
                    </ScrollView>
                )}

                {/* Selected Skills Chips (khi không search) */}
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