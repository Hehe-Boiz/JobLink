import {StyleSheet} from "react-native";

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
        marginBottom: 20,
    },

    inputContainer: {
        backgroundColor: '#FFF',
        borderRadius: 16,
        padding: 16,
        minHeight: 200,
        shadowColor: '#130160',
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.06,
        shadowRadius: 10,
        elevation: 3,
    },
    textInput: {
        flex: 1,
        fontSize: 14,
        color: '#150B3D',
        fontFamily: 'DMSans-Regular',
        lineHeight: 22,
    },

    spacer: {
        flex: 1,
    },

    saveButton: {
        backgroundColor: '#130160',
        borderRadius: 10,
        paddingVertical: 18,
        alignItems: 'center',
        marginBottom: 20,
    },
    saveButtonText: {
        fontSize: 15,
        fontWeight: '700',
        color: '#FFF',
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
    modalTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#FFF',
        marginTop: 20,
        marginBottom: 20,
    },
    modalInputPreview: {
        backgroundColor: 'rgba(255,255,255,0.1)',
        borderRadius: 16,
        padding: 16,
        minHeight: 180,
    },
    modalInputText: {
        fontSize: 14,
        color: 'rgba(255,255,255,0.5)',
        lineHeight: 22,
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