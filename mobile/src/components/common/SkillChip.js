import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CustomText from './CustomText';

const SkillChip = ({
    label,
    onRemove,
    isHighlighted = false,
    showRemoveIcon = true,
}) => {
    return (
        <View style={[styles.chip, isHighlighted && styles.chipHighlighted]}>
            <CustomText style={[styles.chipText, isHighlighted && styles.chipTextHighlighted]}>
                {label}
            </CustomText>
            {showRemoveIcon && (
                <TouchableOpacity
                    onPress={onRemove}
                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                    <MaterialCommunityIcons
                        name="close"
                        size={18}
                        color={isHighlighted ? '#FFFFFF' : '#150A33'}
                    />
                </TouchableOpacity>
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    chip: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#ece8ec',
        // borderWidth: 1,
        // borderColor: '#EAEAEA',
        borderRadius: 8,
        paddingVertical: 11,
        paddingLeft: 11,
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
});

export default SkillChip;