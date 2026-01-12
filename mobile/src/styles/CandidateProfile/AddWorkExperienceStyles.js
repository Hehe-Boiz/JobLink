import {Dimensions, StyleSheet} from "react-native";

const {height: screenHeight} = Dimensions.get('window');

export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9',
    },
    keyboardView: {
        flex: 1,
    },
    content: {
        flex: 1,
        paddingHorizontal: 20,
    },
    scrollContent: {
        paddingBottom: 10,
    },

    backButton: {
        width: 44,
        height: 44,
        justifyContent: 'center',
        marginLeft: -10,
        marginTop: 10,
    },
    backButtonPlaceholder: {
        width: 44,
        height: 44,
        marginLeft: -10,
        marginTop: 10,
    },

    title: {
        fontSize: 18,
        fontWeight: '700',
        color: '#150B3D',
        marginTop: 20,
        marginBottom: 25,
    },

    inputGroup: {
        marginBottom: 20,
    },
    label: {
        fontSize: 16,
        fontWeight: '600',
        color: '#150B3D',
        marginBottom: 10,
    },
    input: {
        backgroundColor: '#FFF',
        borderRadius: 12,
        paddingHorizontal: 16,
        height: 50,
        fontSize: 14,
        color: '#150B3D',
        fontFamily: 'DMSans-Regular',
        borderWidth: 1,
        borderColor: '#E8E8E8',
        justifyContent: 'center',
    },
    inputDisabled: {
        backgroundColor: '#F5F5F5',
    },

    dateRow: {
        flexDirection: 'row',
        gap: 15,
        marginBottom: 20,
    },
    dateInput: {
        flex: 1,
    },
    dateText: {
        fontSize: 14,
        color: '#150B3D',
        fontFamily: 'DMSans-Regular',
    },
    dateTextDisabled: {
        color: '#AAA6B9',
    },

    checkboxRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 25,
    },
    checkbox: {
        width: 22,
        height: 22,
        borderRadius: 6,
        borderWidth: 2,
        borderColor: '#E8E8E8',
        backgroundColor: '#FFF',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    checkboxChecked: {
        backgroundColor: '#130160',
        borderColor: '#130160',
    },
    checkboxLabel: {
        fontSize: 13,
        color: '#524B6B',
    },

    textAreaContainer: {
        backgroundColor: '#FFF',
        borderRadius: 12,
        padding: 13,
        minHeight: 120,
        borderWidth: 1,
        borderColor: '#E8E8E8',
        paddingTop: 8,
    },
    textArea: {
        flex: 1,
        fontSize: 14,
        color: '#150B3D',
        fontFamily: 'DMSans-Regular',
        lineHeight: 22,
    },

    buttonContainer: {
        marginBottom: 80,
        flexDirection: "row",
        gap: 15,
        justifyContent: "space-between",
        padding: 20,
    },
    saveButton: {
        flex: 1,
        backgroundColor: '#130160',
        borderRadius: 10,
        paddingVertical: 18,
        alignItems: 'center',
        justifyContent: 'center',
    },
    saveButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFF',
        letterSpacing: 1,
    },
    removeButton: {
        flex: 1,
        backgroundColor: '#D6CDFE',
        borderRadius: 10,
        paddingVertical: 18,
        alignItems: 'center',
        justifyContent: 'center',

    },
    removeButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFFFFF',
        letterSpacing: 1,
    },
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        justifyContent: 'flex-end',
    },

    modalHeader: {
        flex: 1,
        paddingHorizontal: 20,
    },
    closeButton: {
        width: 44,
        height: 44,
        justifyContent: 'center',
        marginLeft: -10,
        marginTop: 10,
    },

    bottomSheet: {
        backgroundColor: '#FFF',
        borderTopLeftRadius: 30,
        borderTopRightRadius: 30,
        paddingHorizontal: 30,
        paddingBottom: 40,
    },
    handleBarContainer: {
        alignItems: 'center',
        paddingVertical: 15,
        paddingHorizontal: 50,
    },
    sheetHandle: {
        width: 50,
        height: 4,
        backgroundColor: '#E0E0E0',
        borderRadius: 2,
    },
    sheetTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#150B3D',
        textAlign: 'center',
        marginBottom: 10,
    },
    sheetSubtitle: {
        fontSize: 13,
        color: '#524B6B',
        textAlign: 'center',
        marginBottom: 30,
    },
    continueButton: {
        backgroundColor: '#130160',
        borderRadius: 10,
        paddingVertical: 18,
        alignItems: 'center',
        marginBottom: 15,
    },
    continueButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFF',
        letterSpacing: 1,
    },
    undoButton: {
        backgroundColor: '#D6CDFE',
        borderRadius: 10,
        paddingVertical: 18,
        alignItems: 'center',
    },
    undoButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: '#130160',
        letterSpacing: 1,
    },
});