import {View, Image, Animated, Pressable} from 'react-native';
import styles from '../../styles/Candidate/CandidateHomeStyles'
import {MaterialCommunityIcons} from '@expo/vector-icons';
import {TouchableRipple} from 'react-native-paper';
import CustomText from "../CustomText";


const JobCard = ({item, onSavePress, onApplyPress}) => {
    const scaleValue = new Animated.Value(1);
    const bookmarkScale = new Animated.Value(1);

    const animateBookmark = (toValue) => {
        Animated.spring(bookmarkScale, {
            toValue,
            useNativeDriver: true,
            friction: 4,
            tension: 40,
        }).start();
    };

    const onPressIn = () => {
        Animated.spring(scaleValue, {
            toValue: 0.97,
            useNativeDriver: true,
        }).start();
    };

    const onPressOut = () => {
        Animated.spring(scaleValue, {
            toValue: 1,
            useNativeDriver: true,
        }).start();
    };

    return (
        <Animated.View style={{transform: [{scale: scaleValue}]}}>
            <TouchableRipple
                onPress={() => console.log('Job Pressed')}
                onPressIn={onPressIn}
                onPressOut={onPressOut}
                rippleColor="rgba(19, 1, 96, 0.1)"
                style={styles.jobCard}
            >
                <View>
                    <View style={styles.jobCardHeader}>
                        <View style={styles.jobCardLeft}>
                            <View style={styles.logoContainer}>
                                <Image
                                    source={{uri: item.logo}}
                                    style={styles.companyLogo}
                                    resizeMode="contain"
                                />
                            </View>
                            <View style={styles.jobInfo}>
                                <CustomText style={styles.jobTitle}>{item.title}</CustomText>
                                <CustomText style={styles.companyInfo}>
                                    {item.company} • {item.location}
                                </CustomText>
                            </View>
                        </View>
                        <Animated.View style={{transform: [{scale: bookmarkScale}]}}>
                            <TouchableRipple
                                borderless
                                centered
                                onPress={() => onSavePress(item.id)}
                                onPressIn={() => animateBookmark(1.2)}
                                onPressOut={() => animateBookmark(1)}
                                rippleColor="rgba(16, 91, 230, 0.2)"
                                style={{padding: 8, borderRadius: 20}}
                            >
                                <MaterialCommunityIcons
                                    name={item.saved ? "bookmark" : "bookmark-outline"}
                                    size={24}
                                    color={item.saved ? "#105be6ff" : "#95969D"}
                                />
                            </TouchableRipple>
                        </Animated.View>
                    </View>

                    <View style={styles.salaryContainer}>
                        <CustomText style={styles.salary}>
                            {item.salary}
                            <CustomText style={styles.salaryPeriod}>/{item.period}</CustomText>
                        </CustomText>
                    </View>

                    <View style={styles.jobFooter}>
                        <View style={styles.tagsContainer}>
                            {item.tags.map((tag, index) => (
                                <View key={index} style={styles.tag}>
                                    <CustomText style={styles.tagText}>{tag}</CustomText>
                                </View>
                            ))}
                        </View>

                        <Pressable
                            style={({pressed}) => [
                                styles.applyButton,
                                {opacity: pressed ? 0.7 : 1}
                            ]}
                            onPress={() => onApplyPress(item.id)}
                        >
                            <CustomText style={styles.applyButtonText}>Apply</CustomText>
                        </Pressable>
                    </View>
                </View>
            </TouchableRipple>
        </Animated.View>
    );
};

export default JobCard;
