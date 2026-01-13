import React, {useState, useCallback} from 'react';
import {
    View,
    TouchableOpacity,
    ScrollView,
    StyleSheet,
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import {useFocusEffect} from '@react-navigation/native';
import CustomText from '../../components/common/CustomText';
import SkillChip from "../../components/common/SkillChip";

const SkillList = ({navigation, route}) => {
    // Skills ban đầu (có thể từ API hoặc route params)
    const initialSkills = route?.params?.skills || [
        'Leadership', 'Teamwork', 'Visioner', 'Target oriented',
        'Consistent', 'Good communication skills', 'English', 'Responsibility'
    ];

    const [skills, setSkills] = useState(initialSkills);

    // Callback khi quay về từ AddSkill
    const handleSkillsUpdate = useCallback((newSkills) => {
        setSkills(newSkills);
    }, []);

    const handleRemoveSkill = (skillToRemove) => {
        setSkills(skills.filter(skill => skill !== skillToRemove));
    };

    const handleBack = () => {
        // Trả về skills đã cập nhật nếu có callback
        if (route?.params?.onSave) {
            route.params.onSave(skills);
        }
        navigation.goBack();
    };

    const handleChange = () => {
        navigation.navigate('AddSkill', {
            skills: skills,
            onSave: handleSkillsUpdate,
        });
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
                {/* Title với số lượng */}
                <CustomText style={styles.title}>
                    Skill ({skills.length})
                </CustomText>

                {/* Skills Chips */}
                <ScrollView
                    style={styles.scrollView}
                    showsVerticalScrollIndicator={false}
                    contentContainerStyle={styles.scrollContent}
                >
                    <View style={styles.chipsWrapper}>
                        {skills.map((skill, index) => (
                            <SkillChip
                                key={index}
                                label={skill}
                                onRemove={() => handleRemoveSkill(skill)}
                                showRemoveIcon={true}
                                // Bạn có thể tùy chỉnh style container nếu cần thiết thông qua View bao ngoài
                            />
                        ))}
                    </View>
                </ScrollView>

                {/* Change Button */}
                <View style={styles.buttonContainer}>
                    <TouchableOpacity
                        style={styles.changeButton}
                        onPress={handleChange}
                        activeOpacity={0.8}
                    >
                        <CustomText style={styles.changeButtonText}>CHANGE</CustomText>
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
        marginBottom: 24,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        flexGrow: 1,
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
    chipText: {
        fontSize: 13,
        fontWeight: '500',
        color: '#524B6B',
    },
    buttonContainer: {
        paddingVertical: 20,
    },
    changeButton: {
        backgroundColor: '#130160',
        height: 56,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
    },
    changeButtonText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#FFFFFF',
    },
});

export default SkillList;